import os
import sys
import socket
import thread
from collections import deque

# ros imports
import rospy
from std_msgs.msg import String

# constants
N_REC_SIZE = 6

# global variabls
g_tok_q = deque ()
g_host  = socket.gethostbyname (socket.gethostname ())
g_gyro_port     = 4001
g_kinect_port   = 4002

g_pub_kinect    = None
g_pub_gyro      = None

# using ros function
def send_ros (pub, cmd, ts, x, y, z):
    print "ros send: {}:{}:{}:{}:{}".format (cmd, ts, x, y, z)
    sent = cmd + ':' + ts + ':' + x + ':' + y + ':' + z
    pub.publish (sent);

def parse_input (data, pub):

    # add the new input to the token queue
    g_tok_q.extend (data.strip().split (' '));
    
    while len(g_tok_q) > N_REC_SIZE:

        print 'test 0'

        # check 'Go' tag
        tag = g_tok_q.popleft ()
         
        if tag != 'GO':
            print '{}'.format (tag)
            continue

        cmd = g_tok_q.popleft () 
        ts  = g_tok_q.popleft ()
        x   = g_tok_q.popleft ()
        y   = g_tok_q.popleft ()
        z   = g_tok_q.popleft ()
        
        # send via ROS functions
        send_ros (pub, cmd, ts, x, y, z)

def handler (pub, conn, addr):
    
    try:
        
        
        # Keep the client here
        while True:
            print 'handler started'
            # get the new (raw) data
            new_data = conn.recv (256)
            parse_input (new_data, pub)
    except rospy.ROSInterruptException:
        print 'ros interrupt exception'
        pass
            
def gyro_server_thread ():
    
    server = None

    try:
        server = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
        server.bind ((g_host, g_gyro_port))
    except:
        print 'failed to start Mr.Geppetto'
        sys.exit ()
    
    server.listen (10)
    
    while True:
        try:
            conn, addr = server.accept ()
            print 'Connected with ' + addr[0] + ':' + str(addr[1])
            thread.start_new_thread (handler, (g_pub_gyro, conn, addr))
        except:
            print 'Mr.Geppetto(server) is not working'
            server.close ()
            return

def kinect_server_thread ():
    
    server = None

    try:
        server = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
        server.bind ((g_host, g_kinect_port))
    except:
        print 'failed to start Mr.Geppetto'
        sys.exit ()
    
    server.listen (10)
    
    while True:
        try:
            conn, addr = server.accept ()
            print 'Connected with ' + addr[0] + ':' + str(addr[1])
            thread.start_new_thread (handler, (g_pub_kinect, conn, addr))
        except:
            print 'Mr.Geppetto(server) is not working'
            server.close ()
            return

# main function
if __name__ == "__main__":
    
    argc = len (sys.argv) 
    
    if argc == 3:
        g_gyro_port     = int (sys.argv[1])
        g_kinect_port   = int (sys.argv[2])
    elif argc == 1:
        # use default
        pass
    else:
        print 'incorrect params'
        sys.exit ()
        
    print 'Initialize ROS nodes - kinect'
    g_pub_kinect = rospy.Publisher ('kinect', String, queue_size=10)
    rospy.init_node ('kinect', anonymous=True)
    rate = rospy.Rate (10) # 10hz
    
    print 'Initialize ROS nodes - gyro'
    g_pub_gyro   = rospy.Publisher ('gyro',   String, queue_size=10)
    rospy.init_node ('gyro', anonymous=True)
    rate = rospy.Rate (10) # 10hz
    
    print 'Starting Mr.Geppetto server @ {}:{},{}'.format(g_host, g_gyro_port, g_kinect_port)
    thread.start_new_thread (gyro_server_thread, ())
    thread.start_new_thread (kinect_server_thread, ())
    
    