import os
import math
from utils.lru import LRU
from cache.cache import L1Cache, L2Cache
from dram.dram import DRAM
from scratchpad.scratchpad import Scratchpad 

class MemSim:
    def __init__(self):
        self.hit_latency = 1

    def set_params(self,bank_num,bank_row,dim,data_size,
                   l1_way,l1_total_size, l1_line_size,l1_replacement,l1_addr_size,l1_data_size,
                   l2_way,l2_total_size, l2_line_size,l2_replacement,l2_data_size):
        assert l1_line_size%2==0,"Cacheline size is unalign!"
        assert l1_total_size%2==0,"Cacheline size is unalign!"
        assert (l1_data_size>>3)<=l1_line_size, "Data size is too big,it must less than 64bits"
        assert l1_replacement=="PLRU"

        ################## init ####################
        self.dram = DRAM(int(l1_line_size/(l1_data_size/8)))
        self.scratchpad = Scratchpad(bank_num,bank_row,dim,data_size)
        self.l1cache=L1Cache(l1_way,l1_total_size, l1_line_size,l1_replacement,l1_addr_size,l1_data_size,False)
        self.l2cache=L2Cache(l2_way,l2_total_size, l2_line_size,l2_replacement,l1_addr_size,l2_data_size,True)
        
        self.l2cache.backing_mem = self.dram 
        self.l1cache.backing_mem = self.l2cache    
        self.scratchpad.backing_mem = self.l2cache  
        
################### simple API with no detailed info ####################
    def cache_read(self, addr):
        data = self.l1cache.read(addr)
        return data

    def cache_write(self, addr, data):
        self.l1cache.write(addr,data)

    def spm_read(self,addr):
        return self.scratchpad.read(addr)

    def spm_write(self,addr,data):
        self.scratchpad.write(addr,data)

######################### API with detailed info #########################
    # 返回值为 dict:
    # {
    #   'data':          读到的数据,
    #   'l1_hit':        bool, L1是否命中,
    #   'l1_evict_addr': int|None, L1踢出的cacheline地址(None表示无踢出),
    #   'l2_hit':        bool, L2是否命中(L1命中时为False, 因为不访问L2),
    #   'l2_evict_addr': int|None, L2踢出的cacheline地址(None表示无踢出),
    # }
    def cache_read_detail(self, addr):
        return self.l1cache.read_detail(addr)

    # 返回值为 dict (同上, 无'data'字段):
    def cache_write_detail(self, addr, data):
        return self.l1cache.write_detail(addr,data)

    # SPM 一次读会发起多次L2 cacheline访问
    # 返回值为 dict:
    # {
    #   'data':     读到的数据列表,
    #   'l2_infos': list[dict], 每次cacheline访问的L2详情
    #              每个dict: {'hit': bool, 'evict_addr': int|None}
    # }
    def spm_read_detail(self,addr):
        data, l2_infos = self.scratchpad.read_detail(addr)
        return {'data': data, 'l2_infos': l2_infos}

    # 返回值为 dict:
    # {
    #   'l2_infos': list[dict], 每次cacheline访问的L2详情
    # }
    def spm_write_detail(self,addr,data):
        l2_infos = self.scratchpad.write_detail(addr,data)
        return {'l2_infos': l2_infos}



############################## log function ##############################
    def print_info(self):
        l1_miss,l1_hit=self.l1cache.print_info()
        l2_miss,l2_hit=self.l2cache.print_info()
        l1_miss_rate = l1_miss/(l1_miss+l1_hit+1)
        l2_miss_rate = l2_miss/(l2_hit+l2_miss+1)
        total_miss_rate = l1_miss_rate*l2_miss_rate    
        print(f'L1Cache hit {l1_hit}  miss {l1_miss} miss rate {l1_miss_rate}')
        print(f'L2Cache hit {l2_hit}  miss {l2_miss} miss rate {l2_miss_rate}')
        print(f'Total miss rate {total_miss_rate}')
