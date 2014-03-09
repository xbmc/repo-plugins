current_dir=$(pwd)
builddir=basename $(current_dir)

all: zip 
zip:
	echo $(builddir)
	zip -vr plugin.video.putiov2-0.0.3.zip plugin.video.putiov2/ -x *.git* *.idea*
