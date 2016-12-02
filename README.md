# ���ز���װmongodb
�����Linux�£�����mongodb�ķ���
�������Windows�£���mongod --dbpath <���ݿ�Ŀ¼>������mongodb��

������������$ mongo��mongo shell��ȷ����װ�ɹ���

# ��װpython��
pymongo ����ʹ��Mongodb
pymysql ����ʹ��MySQL�ӿ�ץȡ�û�����
paramiko ����ʹ��ssh�ӿ�ץȡ��־����ת��¼
scp��������־�ļ����������ģ�ץȡ��Windows���صĻ��������⡣�����Ҵ��˸�������������е�scp.py

# �����Զ����ű�
$ sh -v auto.sh
����һ�����ص�������������ݿ⣬�����ɱ���
ע�⣬���Ȳ鿴���޸�fetch_logs.py�е��û��������롣
���⣬Ҫץȡ������ĳ��ʱ��ε��������޸���Ӧ�ı�����

# �ֶ����нű�
## ���ز���������
### ���ز������û�����
$ python parse_users.py

### ���ز�������ת��¼
$ python fetch_redirects.py

### ������Ϸ��־
$ python fetch_logs.py "$log_folder" 
���磬���Ҫ����11��10�յģ������� python fetech_logs.py "2016-11-10"

## ���������ļ�
### ������㶨��
��Ҫ����������������ʽ��һ�����ڱ�����������������ʽһ�¡�����Ƚ��ѿ��Ļ������Զ��������ʾ����
$ python loganalyzer.py import --event-def event_def.json 

### ������Ϸ�׶ζ���
������Ϸ�׶εĽ�����˳���������ʽ���������ǿ��԰��׶ν�������ͳ�ơ�
$ python loganalyzer.py import --stage-def stage_def.json  

## ��������
### ����Ĭ������
$ python loganalyzer.py import --defaults 

### �����û�����
������Ϸ���ݿ��е��û����ݡ�Ŀǰֻ�����û����ʹ���ʱ�䡣
$ python loganalyzer.py import --users users.json 

### ������ת��¼
������ת��¼�����ʵ������Ϊ0����㣬���ڼ�����ʧ�ʡ�Ҳ����û����ݿ���бȶԡ�
$ python loganalyzer.py import --redirects redirects.json 

### ������Ϸ��־
������Ϸ��־��������Ҫ��������
$ python loganalyzer.py import -logs "$log_folder" 

## ������־��������Ӧ�ı�
### �������б�
$ python loganalyzer.py update --all

### ������Ϸ�׶α�
Ϊÿ��session������Ϸ�׶Σ���ӽ�����˳�ʱ�䡣
$ python loganalyzer.py update --stages 

### ��������
Ϊÿ��session����־������㣬����������������һ����¼��
$ python loganalyzer.py update --events 

### �����û���
�ϵ���־session��ȱ���û����������������Ը���uuid�²��û���������
$ python loganalyzer.py update --unames 

### ������־session�Ĵ���ʱ��
��Ϊ�е���־��ͷ���ں���ŷ��ͣ�������Ҫ��������session��־������ʱ����ȷ��session�Ĵ���ʱ�䡣
$ python loganalyzer.py update --session-create-time 

### ����Context3D�����Ϣ
$ python loganalyzer.py update --context3d-info 

## ����ͳ�Ƽ���
### ͳ���ڴ���Ϣ
Ŀǰͳ�Ƶ���ÿ����Ϸ�׶ε�Flashƽ���ڴ�ռ��(total memory)��
$ python loganalyzer.py update --memory 

### ͳ��֡��
Ŀǰͳ�Ƶ���ÿ����Ϸ�׶ε�ȥ��һ����͵�֡�����ݼ����ƽ��֡��
$ python loganalyzer.py update --fps 

### ͳ�ƻ���
Ŀǰͳ�Ƶ���ÿ����Ϸ�׶ε���ͻ���
$ python loganalyzer.py update --quality

## �������
### ��session������߽���
���Ȼᱻ����һ���Ʒֿ��У�������session����߽��ȡ�
$ python loganalyzer.py update --session-progress 

### ���û�������߽���
����user����߽��ȡ�
$ python loganalyzer.py update --user-progress 

## ���ɱ���
### �������б���
$ python loganalyzer.py report --all -n "$start_time" "$end_time"
ʹ��-nѡ�������������û��ı���

### �����û�����
��ʼ�ͽ�ֹʱ������"2016-11-10 10:30"�����ĸ�ʽ
$ python loganalyzer.py report --users "$start_time" "$end_time"

### ������ת��¼����
$ python loganalyzer.py report --redirects "$start_time" "$end_time"

### ����session��߽��ȱ���
���ȼƷֿ�Ҳ�ᱻ��ӡ�����������鿴�������㴥����Ϣ��
$ python loganalyzer.py report --session-progress "$start_time" "$end_time"  

### �����û���߽��ȱ���
$ python loganalyzer.py report --user-progress "$start_time" "$end_time"  

### ����session��ʧ����
$ python loganalyzer.py report --session_event "$start_time" "$end_time"  

### �����û���ʧ����
������2�����棬��һ���������û��ģ��ڶ��������û����������ݿ���ע������û�������ת��¼�е����ݿ�û�е��û���
$ python loganalyzer.py report --user-event "$start_time" "$end_time"  

### ���ɼ�����ͳ�Ʊ���
$ python loganalyzer.py report --compatibility "$start_time" "$end_time"  

### �����ڴ�ͳ�Ʊ���
$ python loganalyzer.py report --memory "$start_time" "$end_time"  

### ����֡��ͳ�Ʊ���
$ python loganalyzer.py report --fps "$start_time" "$end_time"  

### ���ɻ���ͳ�Ʊ���
$ python loganalyzer.py report --quality "$start_time" "$end_time"  
