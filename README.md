# 下载并安装mongodb
如果在Linux下，启动mongodb的服务。
如果是在Windows下，用mongod --dbpath <数据库目录>来启动mongodb。

在命令行输入$ mongo打开mongo shell以确定安装成功。

# 安装python库
pymongo 用于使用Mongodb
pymysql 用于使用MySQL接口抓取用户数据
paramiko 用于使用ssh接口抓取日志和跳转记录
scp，由于日志文件名中有中文，抓取到Windows本地的话会有问题。所以我打了个补丁，见打包中的scp.py

# 运行自动化脚本
$ sh -v auto.sh
这是一键下载导入相关数据数据库，并生成报表。
注意，请先查看并修改fetch_logs.py中的用户名和密码。
另外，要抓取和生成某个时间段的数据请修改相应的变量。

# 手动运行脚本
## 下载并解析数据
### 下载并解析用户数据
$ python parse_users.py

### 下载并解析跳转记录
$ python fetch_redirects.py

### 下载游戏日志
$ python fetch_logs.py "$log_folder" 
例如，如果要导入11月10日的，就输入 python fetech_logs.py "2016-11-10"

## 导入配置文件
### 导入埋点定义
主要定义了埋点的正则表达式。一般用于报告的埋点名和正则表达式一致。如果比较难看的话，可以定义埋点显示名。
$ python loganalyzer.py import --event-def event_def.json 

### 导入游戏阶段定义
定义游戏阶段的进入和退出的正则表达式。这样我们可以按阶段进行数据统计。
$ python loganalyzer.py import --stage-def stage_def.json  

## 导入数据
### 导入默认数据
$ python loganalyzer.py import --defaults 

### 导入用户数据
导入游戏数据库中的用户数据。目前只导入用户名和创建时间。
$ python loganalyzer.py import --users users.json 

### 导入跳转记录
导入跳转记录。这个实际上作为0号埋点，用于计算流失率。也会和用户数据库进行比对。
$ python loganalyzer.py import --redirects redirects.json 

### 导入游戏日志
导入游戏日志。这是主要分析对象。
$ python loganalyzer.py import -logs "$log_folder" 

## 分析日志并更新相应的表
### 更新所有表
$ python loganalyzer.py update --all

### 更新游戏阶段表
为每个session分析游戏阶段，添加进入和退出时间。
$ python loganalyzer.py update --stages 

### 更新埋点表
为每个session的日志分析埋点，如果遇到埋点则生成一条记录。
$ python loganalyzer.py update --events 

### 更新用户名
老的日志session会缺少用户名，用这个命令可以根据uuid猜测用户名并更新
$ python loganalyzer.py update --unames 

### 更新日志session的创建时间
因为有的日志表头会在后面才发送，所以需要根据整个session日志的最早时间来确定session的创建时间。
$ python loganalyzer.py update --session-create-time 

### 更新Context3D相关信息
$ python loganalyzer.py update --context3d-info 

## 进行统计计算
### 统计内存信息
目前统计的是每个游戏阶段的Flash平均内存占用(total memory)。
$ python loganalyzer.py update --memory 

### 统计帧率
目前统计的是每个游戏阶段的去除一半最低的帧率数据计算的平均帧率
$ python loganalyzer.py update --fps 

### 统计画质
目前统计的是每个游戏阶段的最低画质
$ python loganalyzer.py update --quality

## 计算进度
### 按session计算最高进度
进度会被计入一个计分卡中，并更新session的最高进度。
$ python loganalyzer.py update --session-progress 

### 按用户计算最高进度
更新user的最高进度。
$ python loganalyzer.py update --user-progress 

## 生成报告
### 生成所有报告
$ python loganalyzer.py report --all -n "$start_time" "$end_time"
使用-n选项用于生产新用户的报告

### 生成用户报告
起始和截止时间请用"2016-11-10 10:30"这样的格式
$ python loganalyzer.py report --users "$start_time" "$end_time"

### 生产跳转记录报告
$ python loganalyzer.py report --redirects "$start_time" "$end_time"

### 生成session最高进度报告
进度计分卡也会被打印。可以用来查看具体的埋点触发信息。
$ python loganalyzer.py report --session-progress "$start_time" "$end_time"  

### 生成用户最高进度报告
$ python loganalyzer.py report --user-progress "$start_time" "$end_time"  

### 生成session流失报告
$ python loganalyzer.py report --session_event "$start_time" "$end_time"  

### 生成用户流失报告
这里有2个报告，第一个是所有用户的，第二个是新用户（包括数据库里注册额新用户，和跳转记录有但数据库没有的用户）
$ python loganalyzer.py report --user-event "$start_time" "$end_time"  

### 生成兼容性统计报告
$ python loganalyzer.py report --compatibility "$start_time" "$end_time"  

### 生成内存统计报告
$ python loganalyzer.py report --memory "$start_time" "$end_time"  

### 生成帧率统计报告
$ python loganalyzer.py report --fps "$start_time" "$end_time"  

### 生成画质统计报告
$ python loganalyzer.py report --quality "$start_time" "$end_time"  
