# ibest
测试自动化脚本为部署测试移动云环境：

COSBench是一个用于测试云对象存储系统的分布式基准测试工具
COSbench包含两个关键组件：

Driver（也称为COSBench驱动或负载生成器）:

负责工作负载生成，向目标云对象存储下发操作，收集性能统计数据。

可以通过访问。

Controller (也称为COSBench控制器):

负责协调drivers集体执行工作负载，收集和汇总来自driver实例的运行时状态或基准测试结果，并接受工作负载提交。

可以通过 访问。
Op-Type：请求类型

Op-Count：请求总次数

Byte-Count：传输数据总量

Avg-ResTime(ms)：从开始上传到传输完成的总时间

Avg-ProcTime(ms)：数据处理的平均时间

Throughput：每秒钟处理的请求数，相当于TPS

Bandwidth(MB/s)：传输带宽

Succ-Ratio：请求成功率



obscmdbench
https://github.com/huaweicloud-obs/obscmdbench
-- 功能说明：
   本工具主要为进行对象存储系统的性能测试功能机，能够自动产生定义的测试数据大小进行对象上传 下载，在性能和执行效率上俱佳。
   自定义配置并发数和上传对象数，自定义测试业务接口，当前支持绝大多数 对象接口操作，
   工具适配华为云 对象存储服务接口， 若对接其他对象接口，做适度接口头域修改就可适配。
   是业内进行性能测试验证的最佳工具.
1. 创建测试帐户：
       配置使用AK SK鉴权，则需要在users.dat文件中按如下格式构造测试帐户供工具读取。（1个或多个，根据需要配置）
      accountName,accessKey,secretKey,
      accountName1,accessKey1,secretKey1,
      accountName2,accessKey2,secretKey2,
      ...

    2. 编辑 config.dat，配置测试模型

    3. 运行，可指定参数，指定的参数覆盖配置文件中的参数
    ./run.py  [测试用例编号] [用户数] [指定加载的配置文件]

    4. 查看结果，目录./result/：
     2013.12.05_06.14.50_HeadBucket_200_brief.txt 表示200用户并发HeadBucket操作最终测试结果。     
     2013.12.05_06.14.50_HeadBucket_200_detail.csv 表示200用户并发HeadBucket操作所有请求的详细结果。
     archive.csv 每次执行后归档的结果。
        ProcessId,UserName,RequestSq,Operation,Start_At,End_At,Latency(s),DataSend(Bytes),DataRecv(Bytes),Mark,RequestID,Response
        0,zz.account.0,1,ListUserBuckets,1394000293.383760,1394000293.409535,0.025775,0,500,,D4B110AFF9760000014490D9C2E4AB2B,200 OK
    
     2014.03.05_06.18.13_MixOperation_2_realtime.txt表示2用户并发MixOperation操作，实时间隔5秒（可配置参数StatisticsInterval）采样周期的性能统计结果。
     NO      StartTime           OK          Requests    ErrRate(%)  TPS       AvgLatency（S）   SendBytes        RecvBytes
     1       03/05 06:18:13.382  279         279         0.0         55.8      0.037           173195           100000
     2       03/05 06:18:18.382  75          75          0.0         15.0      0.13            180061           0
     3       03/05 06:18:23.382  86          86          0.0         17.2      0.116           229280           0
