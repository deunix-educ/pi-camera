dir="server-certs"
FILE="v3.ext"
echo "Creating CA key The passkey is important so remember it"
openssl genrsa -des3 -out ca.key 2048
echo "Created CA Certificate 10 years expiry"
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt
echo "Creating Server key"
openssl genrsa -out server.key 2048
echo "Creating Server certificate"
openssl req -new -out server.csr -key server.key
echo "Signing Server certificate Server certificate"
echo "Common Name should be the FQDN or IP address of the server"
echo "It is what you would use to ping the server"

if [ -f "$FILE" ];then
echo "$FILE exists"
break
else
echo "You need an external file called $FILE to continue"
fi
echo "Press enter to continue"
read var1

if [ ! -f "$FILE" ];then
exit 1
fi

openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 3650 -extfile $FILE
echo "copying files to certs subdirectory"
if [ -d $dir ]
then
 echo "directory Exists"
else
 mkdir $dir
fi
mv *.crt $dir
mv *.key $dir
mv *.csr $dir
mv *.srl $dir
