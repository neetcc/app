# -*- coding: utf-8 -*-

from ryu import cfg



cfg.CONF.register_opts(
    [
        cfg.IntOpt('cookie', default=(1 << 64) - 2,
                       help='cookie value of flow entry for trace route'),
        cfg.StrOpt('metafield', default='metadata',
                       help='metadata field name to identify probe frame'),
        cfg.IntOpt('metavalue', default=(1 << 64) - 2,
                       help='metadata field value to identify probe frame'),
        cfg.StrOpt('ruleclass', default='RuleVlanPcp7',
                       help='rule class to handle probe frame'),
    ],
    'oftroute')


def cookie():
    return cfg.CONF.oftroute.cookie


def metafield():
    return cfg.CONF.oftroute.metafield


def metavalue():
    return cfg.CONF.oftroute.metavalue


def ruleclass():
    return cfg.CONF.oftroute.ruleclass
