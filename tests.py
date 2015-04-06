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
                'eth1_id': 'eni-abc123',
                'eth2_id': 'eni-abc456',
                'route_table_id': 'rtb-0e0ed06b',
                'elastic_ip_allocation_id': 'eipalloc-cc618fa9'
            },
            'eu-west-1b': {
                'eth1_id': 'eni-def123',
                'eth2_id': 'eni-def456',
                'route_table_id': 'rtb-090ed06c',
                'elastic_ip_allocation_id': 'eipalloc-c5618fa0',
            },
            'eu-west-1c': {
                'eth1_id': 'eni-ghi123',
                'eth2_id': 'eni-ghi456',
                'route_table_id': 'rtb-080ed06d',
                'elastic_ip_allocation_id': 'eipalloc-c4618fa1',
            }
        }
        conf = nat_handler.Config(jsondata)
        assert conf.route_table_id('eu-west-1a') == 'rtb-0e0ed06b'
        assert conf.eth1_id('eu-west-1a') == 'eni-abc123'
        assert conf.eth2_id('eu-west-1a') == 'eni-abc456'
        assert conf.elastic_ip_allocation_id('eu-west-1a') == 'eipalloc-cc618fa9'

    def test_complex_without_eip(self):
        jsondata = {
            'eu-west-1a': {
                'eth1_id': 'eni-abc123',
                'eth2_id': 'eni-abc456',
                'route_table_id': 'rtb-0e0ed06b',
            },
            'eu-west-1b': {
                'eth1_id': 'eni-def123',
                'eth2_id': 'eni-def456',
                'route_table_id': 'rtb-090ed06c',
            },
            'eu-west-1c': {
                'eth1_id': 'eni-ghi123',
                'eth2_id': 'eni-ghi456',
                'route_table_id': 'rtb-080ed06d',
            }
        }
        conf = nat_handler.Config(jsondata)
        assert conf.route_table_id('eu-west-1a') == 'rtb-0e0ed06b'
        assert conf.eth1_id('eu-west-1a') == 'eni-abc123'
        assert conf.eth2_id('eu-west-1a') == 'eni-abc456'
        assert conf.elastic_ip_allocation_id('eu-west-1a') == None
