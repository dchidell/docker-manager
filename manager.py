import docker
import argparse
import os
import subprocess

container_dir = 'containers/'
app_dir = 'apps/'

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-u",help="Update container images",action="store_true")
    parser.add_argument("-r",help="Redeploy existing containers / apps",action="store_true")
    parser.add_argument("-p",help="Prune / delete stopped containers",action="store_true")
    parser.add_argument("-d",help="Delete redundant images",action="store_true")
    return parser.parse_args()

def return_txt_file_names(dir):
    files = os.listdir(dir)
    file_names = [file.split(".")[0] for file in files if '.txt' in file]
    return file_names

def exec_command(cmd,success,fail="",failcare=True):
    cmdlist = cmd.split(" ")
    proc = subprocess.Popen(cmdlist,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    err = proc.stderr.read().decode("UTF-8")
    out = proc.stdout.read().decode("UTF-8")

    if failcare:
        if err is "":
            print(success)
            if out:
                return out
            else:
                return True
        else:
            print("{} Reason: {}".format(fail,err))
            return False
    else:
        print(success)
        return out

def find_unused_images(all_images,all_containers):
    used_images = []

    for image in all_images:
        for container in all_containers:
            if image.attrs['Id'] == container.attrs['Image']:
                used_images.append(image)
                break
    unused_images = [image for image in all_images if image not in used_images]
    return unused_images

def get_image_name(image):
    if image.attrs['RepoTags'] == '' or image.attrs['RepoTags'] is None:
        if image.attrs['RepoDigests'] == '':
            return 'ID: '+image.attrs['Id']
        else:
            return ''.join(image.attrs['RepoDigests']).split('@')[0]
    else:
        return ''.join(image.attrs['RepoTags'])

def main():
    client = docker.from_env(version="auto",timeout=30)
    args = parse_args()

    argcount = 0
    for arg in vars(args):
        if getattr(args,arg):
            argcount += 1
    if argcount == 0:
        print("***No Arguments detected, running everything...")


    if args.p or argcount == 0:
        pruned = client.containers.prune()
        if pruned['ContainersDeleted'] == None:
            print("***No containers to be deleted")
        else:
            print("***{} containers deleted. {} bytes of space reclaimed.".format(pruned['ContainersDeleted'].len(),pruned['SpaceReclaimed']))

    if args.u or argcount == 0:
        images = client.images.list()
        count = 0
        for image in images:
            if image.attrs['RepoTags']:
                name = get_image_name(image)
                print("***Updating image "+name)
                try:
                    client.images.pull(name)
                except docker.errors.ImageNotFound:
                    print("***Image not found in docker repo! Unable to update.")
                else:
                    print("***Updated "+name)
                    count += 1
        print("***Update complete. Processed {} images.".format(count))

    if args.r or argcount == 0:
        files = os.listdir(container_dir)
        container_names = [file.split(".")[0] for file in files if '.txt' in file]
        containers = client.containers.list(all=True)
        for container in containers:
            if container.name in container_names:

                print("***Stopping and deleting container: "+container.name)
                container.stop()
                container.remove()
                print("***Re-creating container: "+container.name)
                out = exec_command("bash {}{}.txt".format(container_dir,container.name),"***Container created successfully! Starting up...","***Error detected")
                if out:
                    new_container = client.containers.get(out.strip())
                    new_container.start()

        app_names = os.listdir(app_dir)
        for app in app_names:
            print("***Found app: "+app)
            print("***Stopping app...")
            exec_command("docker-compose -f {}{}/docker-compose.yml stop".format(app_dir,app),"***App stopped successfully!",failcare=False)
            exec_command("docker-compose -f {}{}/docker-compose.yml rm -f".format(app_dir,app),"***App deleted successfully!",failcare=False)
            exec_command("docker-compose -f {}{}/docker-compose.yml up -d".format(app_dir,app),"***App started successfully!",failcare=False)

    if args.d or argcount == 0:
        images = find_unused_images(client.images.list(),client.containers.list(all=True))
        count = 0
        for image in images:
            print('***Redundant Image found: '+get_image_name(image))
            try:
                client.images.remove(image.attrs['Id'])
            except docker.errors.APIError:
                print('***Unable to remove {}. Likely it is a parent image.'.format(get_image_name(image)))
            else:
                count += 1
        print('***{} redundant images removed.'.format(count))

main()
