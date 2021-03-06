
import logging
import struct

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER ,CONFIG_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.topology.api import get_switch, get_link, get_all_host
from ryu.topology import event
import networkx as nx
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp
from ryu.lib import dpid as dpid_lib
from webob import Response
import json
from ryu.app.wsgi import WSGIApplication, ControllerBase, route
#import MyController
url = '/my/{dpid}'


class ProjectController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS ={'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(ProjectController, self).__init__(*args, **kwargs)
        wsgi = kwargs['wsgi']
        wsgi.register(MyController, {'Myapp': self})
        self.mac_to_port = {}
        self.topology_api_app = self
        self.net = nx.DiGraph()
        self.nodes = {}
        self.links = {}
        self.paths={}  # the dict to save the paths of the network[src,dst]:pathlist
        self.datapaths = {}  # dpid: datapath the dict to get the datapath from dpid
        self.hosts = {}  # host_ip:[host_mac, dpid(the switch connected to), in_port(to the switch)]
        # self.discover_thread = hub.spawn(self._discover)
        self.host_mac2ip = {} # host_mac: host_ip
        # the flow entry need to mod [datapath,dst_ip,inport]: outport
        self.flows={}  # [src_ip ,dst_ip] : {[datapath,dst_ip,inport]:outport}
        self.add_dic={}
        self.del_dic={}
        self.mod_dic={}

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        #    Collect datapath information.
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if not datapath.id in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]


    def modflow(self, datapath, table_id, priority, match, instructions, buffer_id=None):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        cookie = cookie_mask = 0
        idle_timeout = hard_timeout = 0
        if buffer_id:
            req = ofp_parser.OFPFlowMod(datapath=datapath, cookie=cookie, cookie_mask=cookie_mask,
                                        table_id=table_id, command=ofp.OFPFC_ADD,
                                        idle_timeout=idle_timeout, hard_timeout=hard_timeout,
                                        priority=priority, buffer_id=buffer_id,
                                        match=match, instructions=instructions)
        else:
            req = ofp_parser.OFPFlowMod(datapath=datapath, cookie=cookie, cookie_mask=cookie_mask,
                                        table_id=table_id, command=ofp.OFPFC_ADD,
                                        idle_timeout=idle_timeout, hard_timeout=hard_timeout,
                                        priority=priority, buffer_id=ofp.OFP_NO_BUFFER,
                                        match=match, instructions=instructions)

        datapath.send_msg(req)

        # delete a flow entry of match in table id
    def delete_entry(self, datapath, table_id, match, instructions):
        ofproto = datapath.ofproto
        req = datapath.ofproto_parser.OFPFlowMod(datapath, 0, 0, table_id,
                                                      ofproto.OFPFC_DELETE, 0, 0, 1,
                                                      ofproto.OFPCML_NO_BUFFER,
                                                      ofproto.OFPP_ANY,ofproto.OFPG_ANY,
                                                      0,match, instructions)
        datapath.send_msg(req)

        # delete all the flow entry in table id
    @staticmethod
    def delete_all(self, datapath,table_id):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match=parser.OFPMatch()
        ints=[]
        req=datapath.ofproto_parser.OFPFlowMod(datapath, 0, 0, table_id,
                                               ofproto.OFPFC_DELETE, 0, 0, 1,
                                               ofproto.OFPCML_NO_BUFFER,
                                               ofproto.OFPP_ANY,ofproto.OFPG_ANY,
                                               0, match, ints)
        print 'del all flow entries in table', 0
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        pkt = packet.Packet(msg.data)
        arp_pkt = pkt.get_protocol(arp.arp)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        in_port = msg.match['in_port']
        if isinstance(arp_pkt, arp.arp):
            print "ARP processing"
            arp_src_ip = arp_pkt.src_ip
            arp_dst_ip = arp_pkt.dst_ip
            src_mac = arp_pkt.src_mac
            # check if the src_ip is the known host
            if arp_src_ip not in self.hosts.keys():
                # add the host to the net and the host dict
                self.net.add_node(arp_src_ip, mac=src_mac, sw=dpid, port=in_port)
                self.hosts[arp_src_ip] = [src_mac, dpid, in_port]
                self.host_mac2ip[src_mac]=arp_src_ip
                self.net.add_edge(arp_src_ip, dpid, {'port': in_port, 'weight': 1})
                self.net.add_edge(dpid, arp_src_ip, {'port': in_port, 'weight': 1})
            if arp_dst_ip in self.hosts.keys():
                #mac = self.hosts[arp_dst_ip][0]
                datapath_id, out_port = self.net.node[arp_dst_ip]['sw'], self.net.node[arp_dst_ip]['port']
                buffer_id = ofproto.OFP_NO_BUFFER
                datapath = self.datapaths[datapath_id]
                in_port = ofproto.OFPP_CONTROLLER
                print "Reply ARP to knew host"
            else:
                # for datapath in self.datapaths:
                out_port = ofproto.OFPP_FLOOD
                buffer_id = msg.buffer_id
                print "Flood ARP"
            actions = [parser.OFPActionOutput(out_port)]
            out = parser.OFPPacketOut(datapath=datapath, buffer_id=buffer_id,
                                      in_port=in_port, actions=actions, data=msg.data)
            datapath.send_msg(out)
            return

        if isinstance(ip_pkt, ipv4.ipv4):
            print "IPV4 processing"
            eth = pkt.get_protocols(ethernet.ethernet)[0]
            if eth.ethertype == ether_types.ETH_TYPE_LLDP:
                # ignore lldp packet
                return
            dst = eth.dst
            src = eth.src
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst
            self.mac_to_port.setdefault(dpid, {})
            if src_ip not in self.net:
                self.net.add_node(src_ip, mac=src_ip)
                self.net.add_edge(dpid, src_ip, {'port': in_port, 'weight': 1})
                self.net.add_edge(src_ip, dpid, {'port': in_port, 'weight': 1})
            if dst_ip in self.net:
                path = nx.shortest_path(self.net, src_ip, dst_ip, weight='weight')
                # add the path to the path dict
                self.paths[src_ip, dst_ip] = path
                self.set_path(path)
                # send back the buffered packets
                out_port = self.net[path[1]][path[2]]['port']
                actions = [parser.OFPActionOutput(out_port)]
                data = msg.data
                out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                          in_port=in_port, actions=actions, data=data)
                datapath.send_msg(out)

    # install flow entry to one path the src and dst is the ethernet mac
    def set_path(self,path):
        src_ip=path[0]
        dst_ip=path[-1]
        datapath=self.datapaths[path[1]]
        parser=datapath.ofproto_parser
        ofproto=datapath.ofproto
        ints=[]
        for index in range(len(path) - 1):
            if index == 0:
                continue
            if index == len(path) - 1:
                continue
            dpid = path[index]
            pre = path[index - 1]
            nxt = path[index + 1]
            in_port = self.net[dpid][pre]['port']
            out_port = self.net[dpid][nxt]['port']
            match = parser.OFPMatch(in_port=in_port,eth_dst=self.hosts[dst_ip][0])
            actions = [parser.OFPActionOutput(out_port)]
            ints.append(parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions))
            self.modflow(self.datapaths[dpid], 1, 100, match, ints)
            # every time set a flow , it will be save in flows
            self.flows[src_ip+dst_ip]= {str(dpid)+dst_ip+str(in_port):out_port}
            print (' add flow:', dpid,
                   ' ipdst:', dst_ip,
                   ' in_port:', in_port,
                   ' out_port:', out_port)
            ints = []



    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # install table-miss flow entry
        #
        # We specify NO BUFFER to max_len of the output action due to
        # OVS bug. At this moment, if we specify a lesser number, e.g.,
        # 128, OVS will send Packet-In with invalid buffer_id and
        # truncated packet data. In that case, we cannot output packets
        # correctly.  The bug has been fixed in OVS v2.1.0.

        match = parser.OFPMatch()
        insts = []
        insts.append(parser.OFPInstructionGotoTable(1))
        # send the miss matched packets from table 0 to table 1
        # another table miss entry will be installed automatically with priority=0
        self.modflow(datapath, 0, 100, match, insts)

        insts = []
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        insts.append(parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions))
        # send the miss matched packets to the controller
        # this is the table miss entry in table 1
        self.modflow(datapath, 1, 0, match, insts)

        match = parser.OFPMatch(vlan_pcp=1, vlan_vid=5|ofproto_v1_3.OFPVID_PRESENT)
        insts = []
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        insts.append(parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                                  actions))
        insts.append(parser.OFPInstructionGotoTable(1))
        # send the copyt of packets with vlan_vid=3 to the controller
        # and then send to the table 1
        self.modflow(datapath, 0, 101, match, insts)
        print ('switch ', datapath.id, 'is ready!')

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        switch_list = get_switch(self.topology_api_app, None)
        host=get_all_host(self.topology_api_app)
        switches = [switch.dp.id for switch in switch_list]
        self.net.add_nodes_from(switches)

        links_list = get_link(self.topology_api_app, None)
        # print links_list
        links = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no, 'weight': 1}) for link in links_list]
        # add_edges src to dst
        self.net.add_edges_from(links)
        links = [(link.dst.dpid, link.src.dpid, {'port': link.dst.port_no, 'weight': 1}) for link in links_list]
        # add_edges dst to src
        self.net.add_edges_from(links)
        print "**********List of links"
        print self.net.edges()

    def compare(self):
        update = {}
        for src_ip in self.hosts.keys():
            for dst_ip in self.hosts.keys():
                if src_ip == dst_ip:
                    continue
                old_path_entry = self.flows[src_ip+dst_ip]
                new_path = nx.shortest_path_length(self.net, src_ip, dst_ip, weight='weight')
                new_path_entry = {}
                for index in range(len(new_path) - 1):
                    if index == 0:
                        continue
                    if index == len(new_path) - 1:
                        continue
                    dpid = new_path[index]
                    pre = new_path[index - 1]
                    nxt = new_path[index + 1]
                    in_port = self.net[dpid][pre]['port']
                    out_port = self.net[dpid][nxt]['port']
                    new_path_entry[dpid,dst_ip,in_port]=out_port
                    if [str(dpid)+dst_ip+str(in_port)] not in old_path_entry:
                        self.add_dic[str(dpid)+ dst_ip+ str(in_port)] = out_port
                    else:
                        if old_path_entry[str(dpid)+ dst_ip+ str(in_port)]!= out_port:
                            self.mod_dic[str(dpid)+ dst_ip+ str(in_port)] = out_port
                for key in old_path_entry.keys():
                    if key not in new_path_entry:
                        self.del_dic[str(dpid)+ dst_ip+ str(in_port)]=out_port # in the matchfield it will be []
                # each paths' update will be saved
                update[src_ip+dst_ip] = [self.add_dic.copy(), self.mod_dic.copy(), self.del_dic.copy()]
                self.add_dic.clear()
                self.mod_dic.clear()
                self.del_dic.clear()
        return update



class MyController(ControllerBase):

    def __init__(self, req, link, data, **config):
        super(MyController, self).__init__(req, link, data, **config)
        self.myapp = data['Myapp']


    @route('my',url,methods=['GET'], requirements=[])
    def show(self,req,**kwargs):
        app=self.myapp
        body=json.dumps({'abc':2})
        return Response(content_type='application/json', body=body)

