##/bin/bash
##author: denghao
##date: 2022-12-29
echo "解压cosbeach安装包到root目录"
cosbeachpag=`find / -name 0.4.2.c4.zip`
if test -z "$cosbeachpag"; then
	echo "没有查找到0.4.2.c4.zip安装包，请上传0.4.2.c4.zip安装包"	
	exit
else
	echo "存在安装包在一下路径： $cosbeachpag 并解压到/root/目录"
	#unzip -zxvf $cosbeachpag -C /root/
	unzip /root/0.4.2.c4.zip  -d /root/
	if [ $? -ne 0 ];then
	    echo "解压0.4.2.c4.zip文件失败"
	else
		echo "解压0.4.2.c4.zip文件成功"
	fi
fi

echo "安装依赖cosbeach环境"
yum install unzip nmap-ncat java curl java-1.8.0-openjdk-devel -y
for i in unzip nmap-ncat java curl java-1.8.0-openjdk-devel  
do  
    rpm -qa | grep $i
	if [ $? -ne 0 ] ;then
	    echo "install $i failed"
	else
	    echo "install $i succeeded"
	fi
done 	

#检查18088端口是否被占用，
#pIDa=`netstat -anltp  | grep 18088 | awk -F :  '{print $2}' | awk '{print $1}'`
pIDa=`netstat -anltp  | grep 18088 `
#echo $pIDa
if [ "$pIDa" != "" ];
then
    echo "18088端口已经被使用"
	#netstat -anltp  | grep 18088
	netstat -anltp  | grep 18088
	ID=`netstat -anltp  | grep 18088  | awk '{print $7}' | awk -F / '{print $1}'`
	exit
else
    echo "启动diver服务"
    cd /root/0.4.2.c4/ && sh start-driver.sh
	if [ $? -ne 0 ] ; then
		echo "启动diver服务失败"
	else
		echo "启动diver服务成功"
		ps -ef  | grep java
		
	fi
fi	

#判断文件是否存在
testFile="/root/host.txt"
if [ -e "$testFile" ]; then
 echo "/root/host.txt文件存在"
else
 echo "/root/host.txt文件不存在"
 exit
fi

##设置driver数量
read -p "设置dirver数量:" num

cat > /root/0.4.2.c4/conf/controller.conf <<EOF
[controller]
drivers = $num
log_level = INFO
log_file = log/system.log
archive_dir = archive
EOF

i=0
while read -r line
do
((i++))
echo [driver$i]
echo name = driver$i
echo url=http://$line:18088/driver
echo -e "\n"
done < /root/host.txt >> /root/0.4.2.c4/conf/controller.conf

if [ $i != $num ] ;then
    echo "dirver数量和host.txt的主机IP数量不一致"
	mv /root/0.4.2.c4/conf/controller.conf /root/0.4.2.c4/conf/controller.conf.bak
    exit
else
	echo "dirver数量和host主机数一致"
fi

#检查19088端口是否被占用，
controllerID=`netstat -anltp  | grep 19088 `
#echo $controllerID
if [ "$controllerID" != "" ];then
    echo "19088端口已经被使用"
	#controlID=`netstat -anltp  | grep 19088  | awk '{print $7}' | awk -F / '{print $1}'`
	controlID=`netstat -anltp  | grep 19088 `
	echo "输出进程19088进程信息：$controlID"
	exit
else
    echo "启动diver服务"
    cd /root/0.4.2.c4/ && sh start-controller.sh
	if [ $? -ne 0 ] ; then
		echo "启动controller服务失败"
	else
		echo "启动controller服务成功"
		ps -ef  | grep java
		
	fi
fi	
