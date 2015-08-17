# -*- coding: utf-8 -*-
from dbaas_zabbix.provider import ZabbixProvider
import logging

LOG = logging.getLogger(__name__)


class DatabaseZabbixProvider(ZabbixProvider):

    def __init__(self, dbaas_api, zabbix_api):
        super(DatabaseZabbixProvider, self).__init__(dbaas_api, zabbix_api)
        self.main_clientgroup = self.main_clientgroup
        self.extra_clientgroup = self.extra_clientgroup

    def create_basic_monitors(self, ):
        clientgroup = self.main_clientgroup
        for host in self.hosts:
            self._create_basic_monitors(host=host.hostname,
                                        ip=host.address,
                                        clientgroup=clientgroup,
                                        alarm="group")

    def delete_basic_monitors(self, ):
        for host in self.hosts:
            self._delete_monitors(host=host.hostname)

    def create_database_monitors(self, **kwargs):
        raise NotImplementedError

    def delete_database_monitors(self,):
        for zabbix_host in self.get_zabbix_databases_hosts():
            self._delete_monitors(host=zabbix_host)

    def get_zabbix_databases_hosts(self,):
        zabbix_hosts = []

        for instance in self.instances:
            zabbix_hosts.append(instance.dns)

        for instance in self.secondary_ips:
            zabbix_hosts.append(instance.dns)

        return zabbix_hosts


class MySQLSingleZabbixProvider(DatabaseZabbixProvider):
    __provider_name__ = 'mysql'
    __is_ha__ = False

    def create_database_monitors(self,):
        clientgroup = self.extra_clientgroup
        for instance in self.instances:
            self._create_database_monitors(host=instance.dns,
                                           dbtype='mysql',
                                           alarm='group',
                                           clientgroup=clientgroup)


class MySQLHighAvailabilityZabbixProvider(DatabaseZabbixProvider):
    __provider_name__ = 'mysql'
    __is_ha__ = True

    def create_database_monitors(self,):
        clientgroup = self.extra_clientgroup
        for instance in self.database_instances:
            params = {'host': instance.dns,
                      'alarm': 'group',
                      'clientgroup': clientgroup,
                      'dbtype': 'mysql',
                      'healthcheck': {'port': '80',
                                      'string': 'WORKING',
                                      'uri': 'health-check/'},
                      'healthcheck_monitor': {'port': '80',
                                              'string': 'WORKING',
                                              'uri': 'health-check/monitor/'}}

            self._create_database_monitors(**params)

        for instance in self.secondary_ips:
            self._create_database_monitors(host=instance.dns,
                                           dbtype='mysql',
                                           alarm='group',
                                           clientgroup=clientgroup)


class MongoDBSingleZabbixProvider(DatabaseZabbixProvider):
    __provider_name__ = 'mongodb'
    __is_ha__ = False

    def create_database_monitors(self):
        clientgroup = self.extra_clientgroup
        for instance in self.instances:
            self._create_database_monitors(host=instance.dns,
                                           dbtype='mongodb',
                                           alarm="group",
                                           clientgroup=clientgroup)


class MongoDBHighAvailabilityZabbixProvider(DatabaseZabbixProvider):
    __provider_name__ = 'mongodb'
    __is_ha__ = True

    def create_database_monitors(self,):
        clientgroup = self.extra_clientgroup
        for instance in self.database_instances:
            self._create_database_monitors(host=instance.dns,
                                           dbtype='mongodb',
                                           alarm="group",
                                           clientgroup=clientgroup)

        for instance in self.non_database_instances:
            self._create_database_monitors(host=instance.dns,
                                           dbtype='mongodb',
                                           alarm='group',
                                           clientgroup=clientgroup,
                                           arbiter='1')


class RedisZabbixProvider(DatabaseZabbixProvider):

    def create_database_monitors(self,):
        clientgroup = []
        if self.main_clientgroup:
            clientgroup.append(self.main_clientgroup)
        if self.extra_clientgroup:
            clientgroup.append(self.extra_clientgroup)

        notes = self.alarm_notes
        params = {
            "notes": notes,
            "regexp": "WORKING",
            "alarm": "group",
            "clientgroup": clientgroup,
        }
        for instance in self.database_instances:
            params["address"] = instance.dns
            params["var"] = "redis-con"
            params["uri"] = "/health-check/redis-con/"
            self._create_web_monitors(**params)

            params["var"] = "redis-mem"
            params["uri"] = "/health-check/redis-mem/"
            self._create_web_monitors(**params)

        for instance in self.non_database_instances:
            params["address"] = instance.dns
            params["var"] = "sentinel-con"
            params["uri"] = "/health-check/sentinel-con/"
            self._create_web_monitors(**params)

    def get_zabbix_databases_hosts(self,):
        zabbix_hosts = []
        for instance in self.instances:
            host = "webmonitor_{}-80-redis-con".format(instance.dns)
            zabbix_hosts.append(host)
            host = "webmonitor_{}-80-redis-mem".format(instance.dns)
            zabbix_hosts.append(host)

        for instance in self.non_database_instances:
            host = "webmonitor_{}-80-sentinel-con".format(instance.dns)
            zabbix_hosts.append(host)

        return zabbix_hosts


class RedisSingleZabbixProvider(RedisZabbixProvider):
    __provider_name__ = 'redis'
    __is_ha__ = False


class RedisHighAvailabilityZabbixProvider(RedisZabbixProvider):
    __provider_name__ = 'redis'
    __is_ha__ = True


class FakeSingleZabbixProvider(DatabaseZabbixProvider):
    __provider_name__ = 'fake'
    __is_ha__ = False

    def create_database_monitors(self, alarm='group'):
        instances = self.instances
        self._create_database_monitors(instances, dbtype='fake', alarm=alarm)


class FakeHAZabbixProvider(DatabaseZabbixProvider):
    __provider_name__ = 'fake'
    __is_ha__ = True

    def create_database_monitors(self, alarm='group'):
        instances = self.instances
        self._create_database_monitors(instances, dbtype='fake', alarm=alarm)
