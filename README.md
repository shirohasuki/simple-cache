
## Getting started in 30 seconds

### *Installing the package*

Typical usage  
![alt text](./img/image.png)

```$  python  test.py -c ./utlis/scale.cfg```  
You can use the cfg file to config the cache parameters

### *Peculiarity*
PLRU replacement only   
Direct mapping,Set associative,Full associative  
Input data size must *smaller* than cacheline size  
No *unalign* support(data size:32bit,so addr must 4byte align)  
L1Cache(write back,write through) and L2Cache(write back,write through inclusive) are supported  
L1Cache's cache_line_size must be equal(less access logic)


The initial version of this repository was completed by [out-of-order55](https://github.com/out-of-order55); this repository builds upon that foundation to further refine it.
