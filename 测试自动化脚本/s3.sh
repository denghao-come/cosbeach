##install s3
##author: denghao
##date: 2023-1-6

echo -e "\e[32m 安装python3依赖包 \e[0m"
yum install epel-release zlib-devel python3 python3-pip  python3-devel  bzip2-devel openssl-devel openssl-static ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel libffi-devel lzma gcc wget -y
if [ $? -ne 0 ];then
	echo -e "\e[32m 依赖组件安装失败检查网络和yum源 \e[0m"
	exit
else
	echo -e "\e[32m python依赖组件安装成功 \e[0m"
fi

##pip3添加国内源
echo -e "\e[32m pip3添加国内源 \e[0m"
mkdir -p /root/.pip
cat <<EOF > /root/.pip/pip.conf
[global] 
index-url = https://pypi.tuna.tsinghua.edu.cn/simple  
#清华大学源
EOF

echo -e "\e[32m 升级pip3 \e[0m"
pip3 install --upgrade pip

echo -e "\e[32m 安装s3依赖包 \e[0m"
pip3 install setuptools requests boto3 botocore psutil gevent s3cmd
if [ $? -ne 0 ];then
	echo -e "\e[32m 依赖组件安装失败检查网络和pip3 \e[0m"
	exit
else
	echo -e "\e[32m s3依赖组件安装成功 \e[0m"
fi


cat << EOF > /root/get_log.yml
---
- name: test
  hosts: all
  tasks:
    - name: find_file
      find:
        paths: /root/
        patterns: "s3.log.*"
        recurse: no
      register: file_name 
    - name: start 
      fetch: 
        dest: /opt/
        src: "{{ item.path }}"
        state: directory 
        flat: yes
      with_items: "{{ file_name.files }}"
EOF


