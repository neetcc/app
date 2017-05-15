from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink
from mininet.node import CPULimitedHost, Host, Node
from mininet.util import irange,dumpNodeConnections
from mininet.log import setLogLevel
from functools import partial
from mininet.cli import CLI
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import RemoteController
class MyTopo( Topo ):
    "Simple topology example."
 
    def __init__( self ):
        "Create custom topo."
        # Initialize topology
        Topo.__init__( self )
	SW=25
	s=[]
	h=[]
	for i in range(SW):
		sw=self.addSwitch('s{}'.format(i+1),mac='00:00:00:00:00:{}'.format(i+1),ip='192.168.2.{}'.format(i+1),listenPort=6630+i)
		s.append(sw)
        for i in range(SW):
		hs=self.addHost('h{}'.format(i+1),ip='192.168.1.{}'.format(i+1))
		h.append(hs)
	linkopts_10 = dict(bw=10, delay='10ms', loss=0, max_queue_size=1000, use_htb=True)
	linkopts_1 = dict(bw=10, delay='1ms', loss=0, max_queue_size=1000, use_htb=True)
	linkopts_2 = dict(bw=10, delay='2ms', loss=0, max_queue_size=1000, use_htb=True)
	linkopts_3 = dict(bw=10, delay='3ms', loss=0, max_queue_size=1000, use_htb=True)
	linkopts_4 = dict(bw=10, delay='4ms', loss=0, max_queue_size=1000, use_htb=True)
	linkopts_5 = dict(bw=10, delay='5ms', loss=0, max_queue_size=1000, use_htb=True)
	self.addLink(s[0],s[1],**linkopts_1)
	self.addLink(s[1],s[3],**linkopts_4)
	self.addLink(s[3],s[2],**linkopts_3)
	self.addLink(s[2],s[5],**linkopts_3)
	self.addLink(s[3],s[4],**linkopts_1)
	self.addLink(s[4],s[2],**linkopts_4)
	self.addLink(s[4],s[6],**linkopts_2)
	self.addLink(s[6],s[7],**linkopts_2)
	self.addLink(s[7],s[5],**linkopts_4)
	self.addLink(s[0],s[2],**linkopts_5)
	self.addLink(s[5],s[10],**linkopts_4)
	self.addLink(s[10],s[11],**linkopts_1)
	self.addLink(s[10],s[9],**linkopts_1)
	self.addLink(s[9],s[8],**linkopts_3)
	self.addLink(s[7],s[8],**linkopts_5)
	self.addLink(s[8],s[14],**linkopts_2)
	self.addLink(s[14],s[13],**linkopts_5)
	self.addLink(s[13],s[12],**linkopts_2)
	self.addLink(s[11],s[13],**linkopts_2)
	self.addLink(s[12],s[0],**linkopts_10)
	self.addLink(s[13],s[21],**linkopts_2)
	self.addLink(s[14],s[16],**linkopts_2)
	self.addLink(s[16],s[15],**linkopts_1)
	self.addLink(s[15],s[8],**linkopts_5)
	self.addLink(s[21],s[20],**linkopts_1)
	self.addLink(s[20],s[19],**linkopts_1)
	self.addLink(s[19],s[18],**linkopts_1)
	self.addLink(s[18],s[17],**linkopts_1)
	self.addLink(s[17],s[16],**linkopts_2)
	self.addLink(s[21],s[23],**linkopts_2)
	self.addLink(s[23],s[22],**linkopts_1)
	self.addLink(s[22],s[24],**linkopts_1)
	self.addLink(s[24],s[18],**linkopts_1)
	for i in range(25):
		self.addLink(h[i],s[i],**linkopts_1)


topos = { 'mytopo': ( lambda: MyTopo() ) }


def simpleTest():
 topo = MyTopo()
 self=Mininet(topo, controller=partial(RemoteController,ip='127.0.0.1',port=6653), host=CPULimitedHost, link=TCLink)
 self.start()
 CLI(self)
 self.stop()
def run():
    "Create network and run the CLI"
    topo = MyTopo()
    self=Mininet(topo, controller=partial(RemoteController,ip='127.0.0.1',port=6653), host=CPULimitedHost, link=TCLink)
    self.start()
    CLI(net)
    self.stop()
if __name__ == '__main__':
        # Tellminiself to print useful information
	setLogLevel( 'info' )
	simpleTest()

