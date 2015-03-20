nat_handler = __import__('nat-handler')

class TestConfig(object):
    def test_simple(self):
        jsondata = {
            'eu-west-1a': 'rtb-0e0ed06b',
            'eu-west-1b': 'rtb-090ed06c',
            'eu-west-1c': 'rtb-080ed06d'
        }
        conf = nat_handler.Config(jsondata)
        assert conf.route_table_id('eu-west-1a') == 'rtb-0e0ed06b'
        assert conf.elastic_ip_allocation_id('eu-west-1a') == None

    def test_complex_with_eip(self):
        jsondata = {
            'eu-west-1a': {
                'route_table_id': 'rtb-0e0ed06b',
                'elastic_ip_allocation_id': 'eipalloc-cc618fa9'
            },
            'eu-west-1b': {
                'route_table_id': 'rtb-090ed06c',
                'elastic_ip_allocation_id': 'eipalloc-c5618fa0',
            },
            'eu-west-1c': {
                'route_table_id': 'rtb-080ed06d',
                'elastic_ip_allocation_id': 'eipalloc-c4618fa1',
            }
        }
        conf = nat_handler.Config(jsondata)
        assert conf.route_table_id('eu-west-1a') == 'rtb-0e0ed06b'
        assert conf.elastic_ip_allocation_id('eu-west-1a') == 'eipalloc-cc618fa9'

    def test_complex_without_eip(self):
        jsondata = {
            'eu-west-1a': {
                'route_table_id': 'rtb-0e0ed06b',
            },
            'eu-west-1b': {
                'route_table_id': 'rtb-090ed06c',
            },
            'eu-west-1c': {
                'route_table_id': 'rtb-080ed06d',
            }
        }
        conf = nat_handler.Config(jsondata)
        assert conf.route_table_id('eu-west-1a') == 'rtb-0e0ed06b'
        assert conf.elastic_ip_allocation_id('eu-west-1a') == None
