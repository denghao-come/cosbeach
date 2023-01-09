	#!/bin/bash

	echo -e "\033[32m ************************测试开始**************************** \033[0m"

	echo -e "\033[33m ------------------------------------------------------------ \033[0m"

	echo "开始创建桶"
	s3cmd  mb  s3://test_001 -c user.s3cfg
	if [ $? -eq 0 ]; then
		echo "创建桶成功"
	else
		echo "failed"
	fi
	echo -e "\033[33m ------------------------------------------------------------ \033[0m"

	echo "上传文件到桶"
	##纠删码put文件
	#s3cmd put test s3://test_001/test -c user.s3cfg --storage-class=STANDARD_IA
	s3cmd put test s3://test_001/test -c user.s3cfg 
	if [ $? -eq 0 ]; then
		echo "上传文件成功"
	else
		echo "上传文件失败"
	fi

	echo -e "\033[33m ------------------------------------------------------------ \033[0m"


	echo "下载文件到本地"
	s3cmd get s3://test_001/test test1  -c user.s3cfg
	if [ $? -eq 0 ]; then
		echo "下载文件成功"
	else
		echo "下载文件失败"
	fi


	echo -e "\033[33m ------------------------------------------------------------ \033[0m"
	echo "复制文件"
	#s3cmd cp s3://test_001/test s3://test_001/test.bak -c user.s3cfg --storage-class=STANDARD_IA
	s3cmd cp s3://test_001/test s3://test_001/test.bak -c user.s3cfg 
	if [ $? -eq 0 ]; then
		echo "复制文件成功"
	else
		echo "复制文件失败"
	fi

	echo -e "\033[33m ------------------------------------------------------------ \033[0m"
	echo "查看桶文件"
	s3cmd ls s3://test_001/ -c user.s3cfg
	if [ $? -eq 0 ]; then
		echo "查看桶文件成功"
	else
		echo "查看桶文件失败"
	fi


	echo -e "\033[33m ------------------------------------------------------------ \033[0m"
	echo "删除文件"
	s3cmd del s3://test_001/test -c user.s3cfg
	s3cmd del s3://test_001/test.bak -c user.s3cfg
	if [ $? -eq 0 ]; then
		echo "删除文件成功"
	else
		echo "删除文件失败"
	fi


	echo -e "\033[33m ------------------------------------------------------------ \033[0m"
	echo "删除桶"
	s3cmd  rb  s3://test_001 -c user.s3cfg
	if [ $? -eq 0 ]; then
		echo "删除桶成功"
	else
		echo "删除桶失败"
	fi

	echo -e "\033[32m ************************测试结束**************************** \033[0m"

