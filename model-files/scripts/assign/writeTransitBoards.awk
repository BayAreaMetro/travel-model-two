BEGIN{

	start_writing=0
	stop_writing=0

}
{

	if(($1 ~/FILEI/) && ($2~/NETI/)){
		print("\n")
		print $0
		print("\n")
		write_header=1
	}


	if(($1 ~/Name/) && ($2~/Mode/) && ($3~/Op/) && ($4~/Stp/) && ($5~/Cr/) && ($6~/Distance/)){
		start_writing = 1
		stop_writing = 0
		if(write_header==1)
			print $0
		write_header=0
	}
  
	if((start_writing==1) && (stop_writing==0) && ($2!="Mode"))
		if(NF==10) print $0
		
	if((NF==6) && ($1~/Total/) && (start_writing==1) && (stop_writing==0)){
#		print $0
		stop_writing=1
	}
	
}