import argparse
import os
import sys
import configparser as cp

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from memsim import MemSim


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', metavar='Config file', type=str,
                        default="../utils/scale.cfg",
                        help="Path to the config file"
                        )

    args = parser.parse_args()
    config = args.c
    if not os.path.exists(config):
        print("ERROR: Config file not found") 
        print("Input file:" + config)
        print('Exiting')
        exit()
    else: 
        config_file = config

    config = cp.ConfigParser()
    config.read(config_file)

    section = 'scratchpad_architecture_presets'
    bank_num = int(config.get(section, 'Bank Num'))
    bank_row = int(config.get(section, 'Bank Row per bank'))
    dim = int(config.get(section, 'Dim'))
    data_size = int(config.get(section, 'Data Size'))

    section = 'l1cache_architecture_presets'
    l1_size = int(config.get(section, 'Total Size'))
    l1_cacheline_size = int(config.get(section, 'Cacheline Size'))
    l1_way = int(config.get(section, 'Way of Associativity'))
    l1_replacement = (config.get(section, 'Way of Replacement'))
    l1_data_size   = int(config.get(section, 'Data Size'))

    section = 'l2cache_architecture_presets'
    l2_size = int(config.get(section, 'Total Size'))
    l2_cacheline_size = int(config.get(section, 'Cacheline Size'))
    l2_way = int(config.get(section, 'Way of Associativity'))
    l2_replacement = (config.get(section, 'Way of Replacement'))
    l2_data_size   = int(config.get(section, 'Data Size'))


    sim = MemSim()
    sim.set_params(bank_num, bank_row, dim, data_size, 
                   l1_way, l1_size, l1_cacheline_size, l1_replacement, 32, l1_data_size, 
                   l2_way, l2_size, l2_cacheline_size, l2_replacement, l2_data_size)
    
############################## spm detailed test ##############################
    # SPM用同一addr发起4次read_line: 第1次cold miss, 后3次hit同一cacheline
    r = sim.spm_read_detail(0x0)
    assert not r['l2_infos'][0]['hit'], "SPM首次访问应L2 miss"
    assert all(info['hit'] for info in r['l2_infos'][1:]), "SPM后续访问应L2 hit"
    print("spm test 1 passed: first miss, rest hit")

    # 不同地址再读, 第1次也应该miss
    r = sim.spm_read_detail(0x100)
    assert not r['l2_infos'][0]['hit'], "SPM新地址首次应L2 miss"
    print("spm test 2 passed: new addr miss")

############################## l1 cache detailed test #########################
    sim2 = MemSim()
    sim2.set_params(bank_num, bank_row, dim, data_size,
                    l1_way, l1_size, l1_cacheline_size, l1_replacement, 32, l1_data_size,
                    l2_way, l2_size, l2_cacheline_size, l2_replacement, l2_data_size)

    # cold miss: L1 miss, L2 miss, 无evict
    r = sim2.cache_read_detail(0x0)
    assert not r['l1_hit'] and not r['l2_hit'], "首次读应L1/L2都miss"
    assert r['l1_evict_addr'] is None and r['l2_evict_addr'] is None, "cold miss不应有evict"
    print("cache test 1 passed: cold miss")

    # 再读相同地址: L1 hit
    r = sim2.cache_read_detail(0x0)
    assert r['l1_hit'], "重复读应L1 hit"
    print("cache test 2 passed: L1 hit")

    # 写后读: 确认数据一致
    sim2.cache_write_detail(0x100, 42)
    r = sim2.cache_read_detail(0x100)
    assert r['l1_hit'] and r['data'] == 42, "写后读应L1 hit且数据为42"
    print("cache test 3 passed: write then read")

    # 制造L1 eviction: 用独立sim, 2-way, 先填满同一index的2个way, 再访问第3个
    sim3 = MemSim()
    sim3.set_params(bank_num, bank_row, dim, data_size,
                    l1_way, l1_size, l1_cacheline_size, l1_replacement, 32, l1_data_size,
                    l2_way, l2_size, l2_cacheline_size, l2_replacement, l2_data_size)
    # offset_bit=4, index_bit=8, 同index地址间隔 = (1<<(4+8)) = 0x1000
    sim3.cache_read_detail(0x0)    # way 0
    sim3.cache_read_detail(0x1000) # way 1, 现在index 0满了
    r = sim3.cache_read_detail(0x2000) # L1应该踢出一个，L2不踢出
    print(r)
    assert not r['l1_hit'] and r['l1_evict_addr'] is not None, "第3个同index地址应触发L1 evict"
    
    sim3.cache_read_detail(0x3000) 
    sim3.cache_read_detail(0x4000) 
    sim3.cache_read_detail(0x5000) 
    sim3.cache_read_detail(0x6000) 
    r = sim3.cache_read_detail(0x7000) # L2 不踢出
    print(r)
    r = sim3.cache_read_detail(0x8000) # L2 应该踢出一个
    print(r)
    print("cache test 4 passed: L1 eviction")
    print("All tests passed!")
