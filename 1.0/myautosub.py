# -*- coding: utf8 -*-
import json,time,sys,re,os,oss2
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
def fileTrans(akId, akSecret, appKey, fileLink) :
	# 地域ID，固定值。
	REGION_ID = "cn-shanghai"
	PRODUCT = "nls-filetrans"
	DOMAIN = "filetrans.cn-shanghai.aliyuncs.com"
	API_VERSION = "2018-08-17"
	POST_REQUEST_ACTION = "SubmitTask"
	GET_REQUEST_ACTION = "GetTaskResult"
	# 请求参数
	KEY_APP_KEY = "appkey"
	KEY_FILE_LINK = "file_link"
	KEY_VERSION = "version"
	KEY_ENABLE_WORDS = "enable_words"
	# 是否开启智能分轨
	KEY_AUTO_SPLIT = "auto_split"
	# 响应参数
	KEY_TASK = "Task"
	KEY_TASK_ID = "TaskId"
	KEY_STATUS_TEXT = "StatusText"
	KEY_RESULT = "Result"
	# 状态值
	STATUS_SUCCESS = "SUCCESS"
	STATUS_RUNNING = "RUNNING"
	STATUS_QUEUEING = "QUEUEING"
	# 创建AcsClient实例
	client = AcsClient(akId, akSecret, REGION_ID)
	# 提交录音文件识别请求
	postRequest = CommonRequest()
	postRequest.set_domain(DOMAIN)
	postRequest.set_version(API_VERSION)
	postRequest.set_product(PRODUCT)
	postRequest.set_action_name(POST_REQUEST_ACTION)
	postRequest.set_method('POST')
	# 新接入请使用4.0版本，已接入（默认2.0）如需维持现状，请注释掉该参数设置。
	# 设置是否输出词信息，默认为false，开启时需要设置version为4.0。
	task = {KEY_APP_KEY : appKey, KEY_FILE_LINK : fileLink, KEY_VERSION : "4.0", KEY_ENABLE_WORDS : False, "max_end_silence" : 200}
	# 开启智能分轨，如果开启智能分轨，task中设置KEY_AUTO_SPLIT为True。
	# task = {KEY_APP_KEY : appKey, KEY_FILE_LINK : fileLink, KEY_VERSION : "4.0", KEY_ENABLE_WORDS : False, KEY_AUTO_SPLIT : True}
	task = json.dumps(task)
	#print(task)
	postRequest.add_body_params(KEY_TASK, task)
	taskId = ""
	try :
		postResponse = client.do_action_with_exception(postRequest)
		postResponse = json.loads(postResponse)
		#print (postResponse)
		statusText = postResponse[KEY_STATUS_TEXT]
		if statusText == STATUS_SUCCESS :
			#print ("录音文件识别请求成功响应！")
			taskId = postResponse[KEY_TASK_ID]
		else :
			print ("录音文件识别请求失败！")
			return
	except ServerException as e:
		print (e)
	except ClientException as e:
		print (e)
	# 创建CommonRequest，设置任务ID。
	getRequest = CommonRequest()
	getRequest.set_domain(DOMAIN)
	getRequest.set_version(API_VERSION)
	getRequest.set_product(PRODUCT)
	getRequest.set_action_name(GET_REQUEST_ACTION)
	getRequest.set_method('GET')
	getRequest.add_query_param(KEY_TASK_ID, taskId)
	# 提交录音文件识别结果查询请求
	# 以轮询的方式进行识别结果的查询，直到服务端返回的状态描述符为"SUCCESS"、"SUCCESS_WITH_NO_VALID_FRAGMENT"，
	# 或者为错误描述，则结束轮询。
	statusText = ""
	while True :
		try :
			getResponse = client.do_action_with_exception(getRequest)
			getResponse = json.loads(getResponse)
			
			statusText = getResponse[KEY_STATUS_TEXT]
			if statusText == STATUS_RUNNING or statusText == STATUS_QUEUEING :
				# 继续轮询
				time.sleep(10)
			else :
				#print (getResponse)
				# 退出轮询
				break
		except ServerException as e:
			print (e)
		except ClientException as e:
			print (e)
	#if statusText == STATUS_SUCCESS :
		#print ("录音文件识别成功！")
	#else :
		#print ("录音文件识别失败！")
	print (statusText)
	return getResponse

def fmTime(timestr):
	h=0
	m=0
	timestr = str(timestr)
	if timestr[0:-3] == '':
		s = '00'
		m = '00'
		h = '00'
	else:
		s = int(timestr[0:-3])%60
		m = (int(timestr[0:-3])-s)%3600//60
		h = int(timestr[0:-3])//3600
		if s<10:
			s = '0'+str(s)
		if m<10:
			m = '0'+str(m)
		if h<10:
			h = '0'+str(h)

	return str(h)+':'+str(m)+':'+str(s)+','+timestr[-3:]


if len(sys.argv)<1:
	print('Usage:myautosub [Uploadfile]')
	sys.exit()

srtsub = ''
i=0

with open('myautosub.cfg','r',encoding='utf-8')as filedd:
	rr_list=filedd.readlines()
con={}
for line in rr_list:
	line=line.replace('\n', '')
	ll=line.split('=')
	con[ll[0]]=ll[1]

print('正在提取16K音频……')
os.system("ffmpeg -i "+sys.argv[1]+' -ar 16000 -y tmp.mp3')

auth = oss2.Auth(con['accessKeyId'], con['accessKeySecret'])
bucket = oss2.Bucket(auth, 'oss-cn-shanghai.aliyuncs.com', 'liaoym')

uploadfile = sys.argv[1].split('\\')
uploadfile=uploadfile[-1]
subname = uploadfile.split('.')
subname.pop()
subname = ".".join(subname)
uploadfile = "tmp.mp3"

print('正在上传本地文件')
bucket.put_object_from_file(uploadfile, uploadfile)
fileLink = bucket.sign_url('GET', uploadfile, 1200, slash_safe=True)

os.system('del '+uploadfile)

#fileLink = sys.argv[1]
print('正在识别字幕……如果文件较大，可能需时较长，请稍候')
# 执行录音文件识别
filetrans = fileTrans(con['accessKeyId'],con['accessKeySecret'], con['appKey'], fileLink)
result = str(filetrans)
sub = eval(result)

if 'Result' not in sub:
	print('Failed, pls CHECK')
	print('正在删除远程文件')
	bucket.delete_object(uploadfile)
	sys.exit()

for item in sub['Result']['Sentences']:
	i+=1
	begintime = fmTime(item['BeginTime'])
	endtime = fmTime(item['EndTime'])
	srtsub += str(i)+'\n'+begintime+' --> '+endtime+'\n'+item['Text']+'\n\n'

with open(subname+'.srt','w',encoding = 'utf-8') as f:
		f.write(srtsub)

print('字幕已完成，文件'+subname+'.srt保存在当前文件夹下')
print('正在删除远程文件')
bucket.delete_object(uploadfile)