##安装python3
##author：denghao
##date：2023-1-5

##安装python3.7
echo "安装python3.7"
yum install zlib-devel bzip2-devel openssl-devel openssl-static ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel libffi-devel lzma gcc wget -y
if [ $? -ne 0 ];then
	echo -e "\e[32m 依赖组件安装失败检查网络和yum源 \e[0m"
	exit
else
	echo -e "\e[32m python依赖组件安装成功 \e[0m"
fi

pythonpag=`find /root/ -name  Python-3.7.7.tgz`
if [ ! -n "$pythonpag" ]; then 
	echo -e "\e[32m 本地没有python3的安装包 \e[0m"
	wget https://www.python.org/ftp/python/3.7.7/Python-3.7.7.tgz -C /root/
	echo -e "\e[32m 解压python-3.7.7 \e[0m"	
	tar -zxvf /root/Python-3.7.7.tgz -C /root/
	echo -e "\e[32m 配置 \e[0m"
	cd /root/Python-3.7.7/ && ./configure prefix=/usr/local/python3
	if [ $? -ne 0 ];then
		echo -e "\e[32m 配置失败 \e[0m"
		exit
	fi
	echo -e "\e[32m 编译和安装 \e[0m"
	cd /root/Python-3.7.7/ && make && make install -j10
	if [ $? -ne 0 ];then
		echo -e "\e[32m 编译和安装失败 \e[0m"		
		exit
	fi
else 
	echo -e "\e[32m 本地有python3的安装包 解压python-3.7.7 \e[0m"
	tar -zxvf /root/Python-3.7.7.tgz -C /root/
	echo -e "\e[32m 配置 \e[0m"
	cd /root/Python-3.7.7/ && ./configure prefix=/usr/local/python3
	if [ $? -ne 0 ];then
		echo -e "\e[32m 配置失败 \e[0m"
		exit
	fi
	echo -e "\e[32m 编译和安装 \e[0m"
	cd /root/Python-3.7.7/ && make && make install -j10
	if [ $? -ne 0 ];then
		echo -e "\e[32m 编译和安装失败 \e[0m"
		exit
	fi
fi 

##设置软链接
echo -e "\e[32m 设置软链接 \e[0m"
ln -s /usr/local/python3/bin/pip3.7 /usr/bin/pip3
ln -s /usr/local/python3/bin/python3.7 /usr/bin/python3

python3 -V
if [ $? -ne 0 ];then
	echo -e "\e[32m python3安装失败 \e[0m"
	exit
else
	echo -e "\e[32m python安装成功 \e[0m"
	python3 -V
fi



##方法二
mkdir -p /root/.pip
cat <<EOF> /root/.pip/pip.conf
[global] 
index-url = https://pypi.tuna.tsinghua.edu.cn/simple  
#清华大学源
EOF
pip3 install --upgrade pip


##安装插件
pip3 install setuptools requests boto3 botocore psutil gevent s3cmd
if [ $? -ne 0 ];then
	echo -e "\e[32m 插件安装失败 \e[0m"
	exit
else
	echo -e "\e[32m 插件安装成功 \e[0m"
	python3 -V
fi






