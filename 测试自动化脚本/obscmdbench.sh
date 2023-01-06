#!/bin/bash
##install python3.7
##author:denghao
##date:2023-1-4
function obs_packeage(){
echo "解压obscmdbench安装包到root目录"
obscmdbenchpag=`find / -name obscmdbench-master.zip`
if test -z "$obscmdbenchpag"; then
	echo "没有查找到obscmdbench-master.zip安装包，请上传obscmdbench-master.zip安装包"	
	exit
else
	echo "存在安装包在一下路径： $obscmdbenchpag 并解压到/root/目录"
	#unzip -zxvf $obscmdbenchpag -C /root/
	yum install unzip -y
	unzip $obscmdbenchpag  -d /root/
	if [ $? -ne 0 ];then
	    echo "解压obscmdbench-master.zip文件失败"
	else
		echo "解压obscmdbench-master.zip文件成功"
	fi
fi
}

function user(){
    echo -e "\e[32m 输入对象存储用户名、ak、sk \e[0m"
    read -p "input username: " username
    read -p "input ak: " ak
    read -p "input sk: "  sk
    echo "$username,$ak,$sk" > /root/obscmdbench-master/users.dat
}

function OSCs() {
##修改链接IP
echo -e "\e[32m 输入对象存储ipv6或者域名 \e[0m"
read -p "input OSCs val:" OSCs
sed -i '10c OSCs = '"${OSCs}"' ' /root/obscmdbench-master/config.dat
}

function testcase() {
##选择脚本运行模式
echo -e "\e[32m 
201  上传文件
202	 下载文件
204	 删除文件 
\e[0m"
read -p "input Testcase :" Testcase
sed -i '16c Testcase = '"${Testcase}"' ' /root/obscmdbench-master/config.dat
}

function buckename(){
##修改存储桶
echo -e "\e[32m 输入创建的桶 \e[0m"
read -p "input BucketName:" BucketName
sed -i '402c BucketNameFixed = '"${BucketName}"' ' /root/obscmdbench-master/config.dat
}

function usedomainname(){
##修改是否启动域名
echo -e "\e[32m 是否启动域名 \e[0m"
read -p "input UseDomainName (请输入True 或者 false ):" UseDomainName
sed -i '418c UseDomainName = '"${UseDomainName}"' ' /root/obscmdbench-master/config.dat
}

function domainname(){
##输入域名
echo -e "\e[32m 输入域名名称 \e[0m"
read -p "input DomainName :" UseDomainName
sed -i '424c DomainName = '"${UseDomainName}"' ' /root/obscmdbench-master/config.dat
}

function objectsize(){
##文件大小字节
echo -e "\e[32m 上传的对象大小（字节） \e[0m"
read -p "input ObjectSize :" ObjectSize
sed -i '192c ObjectSize =  '"${ObjectSize}"' ' /root/obscmdbench-master/config.dat
}

function objectsperbucketperthread(){
##对象数
echo -e "\e[32m 每个并发在每个桶中上传的对象数 \e[0m"
read -p "input ObjectsPerBucketPerThread :" ObjectsPerBucketPerThread
sed -i '197c ObjectsPerBucketPerThread =  '"${ObjectsPerBucketPerThread}"' ' /root/obscmdbench-master/config.dat
}

setup () {
	cat<<-EOF
===================================
    0.全部执行
    1.解压安装包
    2.设置IP
    3.设置脚本运行模式（201 上传、202 下载、204 删除）
    4.输入桶名
    5.是否启动域名
    6.输入域名
    7.设置文件大小（字节）
    8.上传的对象数
    9.创建用户文件
===================================
EOF
    read -p "please input a number：" x
 
case $x in
	0)
		obs_packeage
        user
		OSCs
		testcase
		buckename
		usedomainname
		domainname
		objectsize
		objectsperbucketperthread
	 ;;
    1)
        obs_packeage
    ;;
    2)
    　　OSCs
    ;;
    3)
    　　testcase
    ;;
    4)
    　　buckename
	 ;;
    5)
		usedomainname
	 ;;
	6)
		domainname
	 ;;
	7)
		objectsize
	 ;;
	8)
		objectsperbucketperthread
	 ;;
     9)
        user
     ;;
 
	*)
        echo "valid responses are load unload install uninstall"
        setup
     ;;
esac
 
}
 
setup
