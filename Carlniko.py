import netmiko
import paramiko
import re
import os
import csv
import time
from netmiko.ssh_exception import  NetMikoTimeoutException
from paramiko.ssh_exception import SSHException 
from netmiko.ssh_exception import  AuthenticationException
from getpass import getpass

class carlniko:


   int_regex=re.compile(r'Gi{1}\S*\d/\S*\d')
   ip_regex=re.compile(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
   sw_name = re.compile(r'(.*)\.com')
   switchport_regex = re.compile(r'(trunk|static access)')
   vlan_regex = re.compile(r'[\d]{1,4}')
   Portchannel_regex = re.compile(r'Po{1}\d*')
   net_regex = re.compile(r'directly connected,')
   NAC_regex = re.compile(r'[0-9]{1,3}\.[0-9]{1,3}\.([3][2-9]|[4-5][0-9]|130|150)\.[0-9]{1,3}')

   ###############################################################################################################################
   #                                                                                                                             #
   #                 Return True If the port is trunk  and receive Paramiko session.connect  object                              #
   #                                                                                                                             #
   ###############################################################################################################################

   def validateTrunk(self,port,ejecutar):
     try:
        #print("entro a validateTrunk")
        switchport_regex = re.compile(r'(trunk|static access)')
        ejecutar.send("         show interface "+port+" switchport | i Administrative Mode\n")
        time.sleep(5)
        mode = ejecutar.recv(65535).decode(encoding='utf-8')
        #print(mode)
        access = re.search(switchport_regex,mode)
        #print(access.group())
        if access.group()=="trunk":
          #print(mode.group())
          return True
        else:
          #print(output)
          return False
     except:
       return "error: \n"+port 

   ###############################################################################################################################
   #                                                                                                                             #
   #                 Return Mac address of the host and receive IP address and  Netmiko ConnectionHandler object                 #
   #                                                                                                                             #
   ###############################################################################################################################


   def getMac(self,ip,ejecutar):##get the mac address linked in a IP address using show ip arp
      try:
         mac_regex=re.compile(r'[0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4}')
         
         ejecutar.send(f"            ping {ip}\n")
         time.sleep(2)
         output = ejecutar.recv(65535).decode(encoding='utf-8')
         #print(output) 
         ejecutar.send("           show ip arp "+ip+"\n")
         time.sleep(2)
         output = ejecutar.recv(65535).decode(encoding='utf-8')
         #print(output)
         match_mac = re.search(mac_regex,output) #search the mac address on the output and find it with more text
         mac_add=match_mac.group() #mac.group isolte only the mac address found
         return mac_add
      except:
         return "Mac address not found\n"

   ###############################################################################################################################
   #                                                                                                                             #
   #                 Return port number of the host and receive MAC address and  Netmiko ConnectionHandler object                #
   #                                                                                                                             #
   ###############################################################################################################################


   def getPort(self,mac,ejecutar): 
    try:
       int_regex=re.compile(r'(Gi|Fa|Eth){1}\S*\d/\S*\d')
       Portchannel_regex = re.compile(r'Po{1}\d*')
       ejecutar.send("                       show mac add add "+mac+"\n")
       time.sleep(2)
       show_mac = ejecutar.recv(65535).decode(encoding='utf-8')
      # print(show_mac)
       match_int = re.search(int_regex,show_mac)#search the port on the output and find it with more text
       if not match_int:
           match_int = re.search(Portchannel_regex,show_mac)
           return match_int.group()
       return match_int.group()#.group method isolte only the Port ID found
    except:
       return "An error has been ocurred in getPort:\n"

   ###############################################################################################################################
   #                                                                                                                             #
   #                 Return switch name of a neighboor using show cdp neighnoor , it receives port number and                    #
   #                 Netmiko ConnectionHandler object                                                                            #
   #                                                                                                                             #
   ###############################################################################################################################


   def getSwitchName(self,port,ejecutar): 
    try:
       sw_name = re.compile(r'Device ID: .+')
       ejecutar.send("                          show cdp nei "+port+" detail\n")
       time.sleep(2)
       show_cdp = ejecutar.recv(65535).decode(encoding='utf-8')
       #print(show_cdp)
       cdp=re.search(sw_name,show_cdp)
       cdp = cdp.group()
       cdp = cdp.replace("Device ID:","")
       return cdp
    except:
       return "Not name found: "

   ###############################################################################################################################
   #                                                                                                                             #
   #                 Return switch IP address of a neighboor using show cdp neighnoor , it receives port number and              #
   #                 Netmiko ConnectionHandler object                                                                            #
   #                                                                                                                             #
   ###############################################################################################################################

   def getIPSwitch(self,port,ejecutar):
    try:
       ip_regex=re.compile(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
       ejecutar.send("       show cdp nei "+port+" detail\n")
       time.sleep(3)
       show_cdp = ejecutar.recv(65535).decode(encoding='utf-8')
      # print(show_cdp)
       cdp=re.search(ip_regex,show_cdp)
       return cdp.group()
    except:
       return "Not ip address switch found \n"

   ###############################################################################################################################
   #                                                                                                                             #
   #                 Return VLAN of the port and receive port number and  Netmiko ConnectionHandler object                       #
   #                                                                                                                             #
   ###############################################################################################################################

   def getVLAN(self,port,ejecutar):
    try:
      if carlniko.validateTrunk(self,port,ejecutar) == False:
        vlan_regex = re.compile(r'Access Mode VLAN: [\d]{1,4} ')
        ejecutar.send("                                      show interface "+port+" switchport | i Access Mode VLAN\n")
        time.sleep(2)
        show_int_access = ejecutar.recv(65535).decode('UTF-8')
        vlan = re.search(vlan_regex, show_int_access)
        vlan = vlan.group()
        vlan = vlan.replace("Access Mode VLAN: ","")
       # print("variable show int access "+show_int_access+" and vlan "+vlan)
        return vlan
      return "trunk"
    except:
      return "error: \n"
    
   ###############################################################################################################################
   #                                                                                                                             #
   #                 Return TRUE If the IP address belongs to network space where connection handler is sent                     #
   #                 Connection must be in a backbone Layer 3 device, this method works when you want to                         #
   #                 figure it out If where is the gateway of the IP address given                                               #
   #                                                                                                                             #
   ###############################################################################################################################

   def validateNetwork(self,ip,ejecutar):
       try: 
           net_regex = re.compile(r'directly connected,')
           x = re.findall("ASA",carlniko.getPID(self,ejecutar))
           if x:
               ejecutar.send(f" show route {ip}\n")
               time.sleep(1)
               show_ip_route = ejecutar.recv(65535).decode('UTF-8')
           else:
               ejecutar.send(f" show ip route {ip}\n")
               time.sleep(1)
               show_ip_route = ejecutar.recv(65535).decode('UTF-8') 
           route = re.search(net_regex,show_ip_route)
           
           if route:
               return True
           else:
               return False
       except:
         print ("Error  Validate Network") 


   ###############################################################################################################################
   #                                                                                                                             #
   #                 Return hostname of the switch  you send the connection handler                                              #
   #                                                                                                                             #
   ###############################################################################################################################

   def getSelfName(self,ejecutar):
       exp = re.compile(r'hostname .+')
       ejecutar.send("                         show run | i hostname\n")
       time.sleep(15)
       show = ejecutar.recv(65535).decode('UTF-8')
       #print(show)
       show = re.search(exp,show)
       show = show.group()
       show = show.replace("hostname","")
       return show 

   ###############################################################################################################################
   #                                                                                                                             #
   #                 Return IP address of the switch  you send the connection handler                                            #
   #                                                                                                                             #
   ###############################################################################################################################

   def getSelfIpAddress(self,ejecutar): #Return the ip addessess of the switch you send the connection
       try:
           ips_regex = re.compile(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\/32')
           ejecutar.send("                                   show ip route connected\n")
           time.sleep(2)
           show = ejecutar.recv(65535).decode('utf-8')
           #print(show)
           ips = re.search(ips_regex,show)
           return ips.group()
       except:
           print("Error en metodo getSelfIpAddresses")

   ###############################################################################################################################
   #                                                                                                                             #
   #                 This method returns the gateway's IP address of a host's IP given                                           #
   #                 This method receives as paramters, IP of the host, connection handler                                       #
   #                 of the backbone switch/router, username, password, enable password                                          #
   #                                                                                                                             #             
   #                                                                                                                             #
   ###############################################################################################################################
   
   #def getGateway(self,ip,conn,username,password,secret,ipSw): 
   #    try:
    #       lista = []
     #      valid = False
      #     while not carlniko.validateNetwork(self,ip,conn):
       #        contador = 1
        #       ipSw = carlniko.getNextHop(self,ip,conn)
         #      if contador == 1:
    #              device = {"username":username,"password":password,"secret":secret}
     #             lista.append(device)
      #         device = carlniko.validateSSHConection(self,lista,ipSw)
       #        if not device:
        #           cont = 0
         #          while cont<3 and carlniko.validateSSHConection(self,lista,ipSw)==False:  
          #             cont+=1
           #            device = carlniko.askCredentials(self,ipSw)
            #           lista.append(device)
             #      if cont >=3:
              #         return "Error to connect Via SSH in device "+ipSw
              # ios_device = {"device_type": "cisco_ios",
   #               "ip":ipSw,
    #              "username":device.get("username"),
     #             "password":device.get("password"),
      #            "secret":secret,
       #           'global_delay_factor': .01
        #         }
         #      conn.disconnect()
          #     conn = netmiko.ConnectHandler(**ios_device)
           #    conn.enable()
            #   contador +=1
  #         return ipSw     
   #    except:
    #      return " Error en getGateway"
      

   ###############################################################################################################################
   #                                                                                                                             #
   #                 Return the part number of the switch where connection is given                                              #
   #                                                                                                                             #
   ###############################################################################################################################

   def getPID(self,ejecutar):
     try:
       PID_regex = re.compile(r'PID: .+, V')
       ejecutar.send("show inven | i PID:\n")
       time.sleep(1)
       show_PID   = ejecutar.recv(65535).decode('UTF-8')
       #print("show_PID: "+show_PID)
       output = re.search(PID_regex,show_PID)
       output =  output.group()
       output = re.sub("PID:","",output)
       output = re.sub(", V","",output)
       return output
     except:
       return "Error en getPID" 

   ###############################################################################################################################
   #                                                                                                                             #
   #                 Return TRUE If the host's IP address is available for NAC configuration                                     #
   #                 The IP networks available for NAC policy must be defined by user                                            #
   #                 The method receives ip address of the host and the connection handler                                       #
   #                                                                                                                             #
   ###############################################################################################################################

 #  def validateNACPossible(self,ip,conn):
  #     try:
           ##########################################################################################################
           #            You must define the RegEx. Include into RegEx  all the IP segments                          #
           #            that are available for NAC policy                                                           #
           ##########################################################################################################
 #          NAC_regex = re.compile(r'') 
  #         PID = carlniko.getPID(self,conn)
   #        PID = re.findall("ASA", PID)
    #       BAND = True
     #      ip2 = re.findall(NAC_regex,ip)
      #     if  ip2:
       #       BAND = False
        #   if PID or BAND:
         #      return False
          # return True
    #   except:
     #      return "ERROR"

   ###############################################################################################################################
   #                                                                                                                             #
   #                 Return TRUE If credential given are correct.                                                                #
   #                                                                                                                             #
   ###############################################################################################################################
   
   def validateCredentials(self,host,username,password):
       try:
           #print("entro a validar credenciales")
           session = paramiko.SSHClient()
           session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
           session.connect(hostname=host,port=22,username=username,password=password)
           return True
       except(AuthenticationException):
           return False

   ###############################################################################################################################
   #                                                                                                                             #
   #                 This method makes ask for credentials      .                                                                #
   #                                                                                                                             #
   ###############################################################################################################################
   
  # def askCredentials(self,ip):
   #    print("Invalid login for "+ip)
    #   username = input("Enter your SSH username: ")
     #  password = getpass()
      # secret = "J1c4m4@2016"
       #ios_device = {    
        #  "username":username,
         # "password":password,
          #"secret":secret

           # }
      # return ios_device

   ###############################################################################################################################
   #                                                                                                                             #
   #                 Returns next hop IP address, it works sending IP address of a host and connection handdler                  #
   #                 If backbone connection handdler is the gateway, the method will return own IP address                       #
   #                                                                                                                             #
   ###############################################################################################################################

   def getNextHop(self,ip,ejecutar):
          ipx_regex=re.compile(r'\* [0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
          x = re.findall("ASA",carlniko.getPID(self,ejecutar))
          if x:
            ejecutar.send(f" show route {ip}\n")
            time.sleep(1)
            show_ip_route = ejecutar.recv(65535).decode('utf-8')
          else:
            ejecutar.send(f" show ip route {ip}\n")
            time.sleep(1)
            show_ip_route = ejecutar.recv(65535).decode('utf-8')
          ipSw = re.search(ipx_regex,show_ip_route)
          ipSw = ipSw.group()
          #print(ipSw)
          ipSw=ipSw.replace("* ","")
          return ipSw
  

   ###############################################################################################################################
   #                                                                                                                             #
   #                 This method create a file named neighboors                                                                  #
   #                 That include all the neighboors in  a txt                                                                   #
   #                                                                                                                             #
   ###############################################################################################################################


   def getAllNeighboors(self,ejecutar):
     try:
       ejecutar.send("show cdp nei det | i Device\n")
       time.sleep(0.5)
       show_cdp = ejecutar.recv(65535).decode('utf-8')
       return show_cdp
       #with open("neighboors.csv","w+") as f:
        #  f.write(show_cdp)
     except:
       return "Error getAllNeighboors"


    ###############################################################################################################################
   #                                                                                                                             #
   #                 This method create a file named neighboors Platform ID                                                      #
   #                 That include all the neighboors in  a txt                                                                   #
   #                                                                                                                             #
   ###############################################################################################################################



   def getAllNeighboorsPlatformID(self,ejecutar):
     try:
       
       ejecutar.send("show cdp nei det | i Platform\n")
       time.sleep(0.5)
       show_cdp = ejecutar.recv(65535).decode('utf-8')
       return show_cdp
       #with open("Platform.csv","w+") as f:
        #  f.write(show_cdp)
     except:
       return "Error getAllNeighboors"