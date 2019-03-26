#!/bin/bash

FILE="lldpd.conf"

DIR="$/etc/fos/lldpd/"
cd $DIR

if [ -f "$FILE" ]; then
	rm $FILE
fi

echo "configure system chassisid $(cat /etc/machine-id)" >> $FILE
echo "configure system hostname $(hostname)" >> $FILE
echo "configure system description fog05" >> $FILE
echo "configure lldp portidsubtype macaddress" >> $FILE

#echo "configure system interface pattern $IFACE" >> $FILE
for IFACE in $(ls /sys/class/net/ | grep -v lo); do
	echo "configure ports $IFACE lldp portdescription $IFACE" >> $FILE
done
