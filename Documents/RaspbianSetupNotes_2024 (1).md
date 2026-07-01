# <a name="what_is_this"></a>What is This?
These are the steps needed to configure an initial (original) Raspbian image to support the UAS-SAR course.

This is an evolving document so please version control it so that changes are tracked particularly in regard to versioning of related software/hardware.

# <a name="change_log"></a>Change Log
- 2024-06-24
    - Remove Lincoln LAN, update install instructions for newer packages.
    - Change Etcher to Raspberry Pi Imager
- 2019-04-30
    - Initial document

# <a name="required_items"></a>Required Items
1. Computer with:
    1. microSD card reader
    2. ethernet port and ethernet cable, OR wired keyboard+mouse and display
    3. `python` (Tested on 3.11) with virtualenv (`venv`)
2. Micro SD card w/ at least 16 GB capacity ([Amazon](https://www.amazon.com/Sandisk-Ultra-Micro-UHS-I-Adapter/dp/B073K14CVB/)); be sure to get it scanned at ISD or security before inserting it into a Lab machine
3. [Raspberry Pi Model 3B](https://www.newark.com/raspberry-pi/raspberrypi3-modb-1gb/sbc-raspberry-pi-3-mod-b-1gb-ram/dp/77Y6520) (or newer)
4. Ethernet connection and cable
5. `git` and `scp`

# <a name="steps"></a>Steps
These steps are listed in order and without omission. This means there will be redundancy and reversals of steps along the process.


### Imaging the Raspberry Pi
1. Follow instructions on the [Raspberry Pi website](https://www.raspberrypi.com/software/) for installing the Raspberry Pi imager.
2. Launch the imager and image the microSD card.
    1. Select the appropriate Pi model
    2. Use 64-bit Raspberry Pi OS
        - Note: Tested with 2024-03-15 release [Link](https://downloads.raspberrypi.com/raspios_arm64/images/raspios_arm64-2024-03-15/2024-03-15-raspios-bookworm-arm64.img.xz)
    3. After hitting "Next", choose to apply OS customization settings.
        - Set the username and password, to `sardemo` and `s@Rdemo` respectively.
        - Check off "Enable SSH" and select "Use password authentication"
        - Set the locale to America/New\_York, keyboard type us.
    4. Format the SD card. Don't eject it!
3. Configure static IP for headless setup.
    - In the SD card, edit `cmdline.txt`. At the end of the line, add the following:
    ```
    ip=192.168.1.1
    ```
    Make sure there is a space between the end of the previous text and `ip`.
4. Insert SD card into the pi and power it up!

### Connect to the Raspberry Pi (Headless mode)
These instructions are for setting up the Raspberry Pi in full headless mode (no keyboard/mouse and display).
Follow these if your computer has an ethernet port but you don't have a spare hardware (or are lazy idk)
1. Configure your computer's IP address.
    Under Network Settings (or something of the sort), Ethernet, configure the following:
    - IP assignment: manual
    - IPv4 address: `192.168.1.10`
    - IPv4 mask: `255.255.0.0`

    These settings might cause you to lose internet connection; for steps that require your computer
    to have internet connection, you may have to reset this
2. Connect to the raspberry pi
    1. Install `ssh`
    2. Connect to the pi via `ssh`
        - user: `sardemo`, password: `s@Rdemo` as configured above

### Connect to the Raspberry Pi (Keyboard mode)
TODO: I didn't do this to set up the pi

### Connect the Pi to the internet
TODO: I didn't do this step to set up the pi.

### Configure sudo password on the pi
1. Enter the following command:
    ```
    sudo visudo /etc/sudoers.d/010_pi-nopasswd
    ```
2. Remove `NOPASSWD:` from the only line in the file. It should look like this when you're done:
    ```
    sardemo ALL=(ALL) ALL
    ```
3. Save and exit the editor

### Quality of life changes
1. Add the following lines to the end of `~/.bashrc`:
    ```
    alias l=ls
    alias ll='ls -l'
    alias la='ls -a'
    ```

### <a name="packages"></a>Install Required Software/Packages
1. Install `hostapd`
	1. Search for the latest *stable* build of `hostapd` on the [Debian package repo](https://packages.debian.org/search?keywords=hostapd&searchon=names&arch=armhf&suite=stable&section=all)
	2. Replacing `name` with the found name (refer to [Version Information](#version_info) for one found at the time of this document's last update), enter `sudo apt install name`
2. Install `dnsmasq`
	1. Search for the latest *stable* build of `dnsmasq` on the [Debian package repo](https://packages.debian.org/search?keywords=dnsmasq&searchon=names&arch=armhf&suite=stable&section=all)
	2. Replacing `name` with the found name (refer to [Version Information](#version_info) for one found at the time of this document's last update), enter `sudo apt install name`
3. Install `libjpeg-dev`
	1. Search for the latest *stable* build of `libjpeg-dev` on the [Debian package repo](https://packages.debian.org/search?keywords=libjpeg&searchon=names&arch=armhf&suite=stable&section=all)
	2. Replacing `name` with the found name (refer to [Version Information](#version_info) for one found at the time of this document's last update), enter `sudo apt install name`
4. Install `libatlas3-base`
	1. Search for the latest *stable* build of `libatlas3-base` on the [Debian package repo](https://packages.debian.org/search?keywords=libatlas3-base&searchon=names&arch=armhf&suite=stable&section=all)
	2. Replacing `name` with the found name (refer to [Version Information](#version_info) for one found at the time of this document's last update), enter `sudo apt install name`

### Installing Optional Software/Packages
1. Install [Vim](https://www.vim.org/) and tmux; enter `sudo apt install vim tmux`

### Installing packages without Pi internet connection
1. Get the install URLs
    1. Connect to the Pi over ssh
    2. Run the following command on the pi to grab urls needed to install a few useful libraries:
        - `hostapd`, `dnsmasq`, `dhcpcd`, and `iptables` for setting up wireless connection
        - `libjpeg`, `libatlas3`, and `libopenblas-dev` for compute
        - `cmake`, `cython3`, `gfortran`, and `pkg-config` for building
        - `libfreetype6-dev` for build dependency
        - `vim`, `code`, and `tmux` for quality of life
    ```
    sudo apt-get install hostapd dnsmasq dhcpcd iptables libjpeg-dev libatlas3-base cmake gfortran pkg-config libfreetype6-dev vim code tmux -qq --print-uris | cut -d\' -f3 > install_urls.txt
    ```
    3. On the local computer, open a terminal
    4. Run the following command to copy the install urls over to the local computer:
    ```
    scp sardemo@192.168.1.1:~/install_urls.txt .
    echo "http://deb.debian.org/debian/pool/main/o/openblas/libopenblas-base_0.3.5+ds-3_arm64.deb" >> install_urls.txt
    echo "http://deb.debian.org/debian/pool/main/o/openblas/libopenblas-dev_0.3.5+ds-3_arm64.deb" >> install_urls.txt
    ```
2. Download packages on your local computer
- You will probably have to reset your computer's IP assignment back to "Automatic (DHCP)" for this step, for it to have internet access
    1. Create a new folder and `cd` into it
    ```
    mkdir install
    cd install
    ```
    2. Grab all the install files on your computer
        ```
        wget -i ../install_urls.txt
        ```
3. Install packages onto the PI
    1. Copy the install files to the Raspberry Pi
        - Like above, you might have to set the computer's IP back to manual
        ```
        cd ../
        scp -r install sardemo@192.168.1.1:~/
        ```
    2. Connect to the pi and install packages!
    ```
    # on your computer:
    ssh sardemo@192.168.1.1

    # on the pi:
    cd install
    dpkg -i *.deb
    ```
4. (Optional) Configure `vim` and `tmux`
    1. Create a simple tmux configuration using the following command:
    ```
    echo "set -g mouse on" >> ~/.tmux.conf
    ```
    2. Create a simple vim configuration using the following commands:
    ```
    echo "set ts=4 sw=4 smarttab expandtab autoindent preserveindent" >> ~/.vimrc
    echo "syntax on" >> ~/.vimrc
    ```

### Creating the Virtual Environment
1. Browse to the home directory; enter `cd ~`
2. Create the environment; enter `python3 -m venv uassar_env`
3. Add environment auto-activation to the terminal startup script
    Run the following command:
    ```
    echo "source ~/uassar_env/bin/activate" >> ~/.bashrc
    ```
4. Activate the environment
	1. Enter `source ./uassar_env/bin/activate`
	2. Should see `(uassar_env) uassar@raspberrypi:~ $`

### Installing Python Packages (without internet connection)
1. Create a package requirements file named `uassar_requirements.txt` with the following content:
	```
	matplotlib
	numpy
	pyserial
	pyyaml
	scikit-image
	scipy

    Cython
    cppy
    pybind11
    pythran
    meson
    meson_python
    setuptools
    setuptools_scm
	```
2. Create and activate virtualenv on the local machine
    ```
    python3 -m venv env
    source env/bin/activate
    ```
3. Install all the packages into the virtualenv, and then save the full list of dependencies into a new file
    ```
    pip install -r uassar_requirements.txt
    pip freeze > requirements_full.txt
    ```
4. Download all the libraries needed into a separate folder, using the internet connection on your own machine
    ```
    mkdir python_install; cd python_install
    pip download --python-version=3.9 --platform=linux_aarch64 r ../requirements.txt
    ```
5. Copy the `python_install` folder to the pi
    ```
    cd ../
    scp -r python_install sardemo@192.168.1.1:~/
    ```
6. `ssh` back into the pi and install everything in the `python_install` folder
    ```
    ssh sardemo@192.168.1.1
    cd python_install
    ```
    - Note: this is a huge pain in the ass
    - Unpack all the zipped packages by running the following command in the `python_install` folder: `ls *.tar.gz | xargs -L1 tar -xvzf`
    - Any package that is not zipped can be installed directly, using `pip install <package_filename_ending_in.whl>`
        - However, some of them (specifically `tomli`, among others) depend on some built packages
    - The packages that came in a zip have to be installed manually, by `cd`-ing into their folders and running the following command:
        `pip install --no-build-isolation .`
        - If you run into errors, the most likely reason is that there are packages which depend on others that are not yet installed.
          You will probably have to install a few of the wheels first, then install numpy, then install everything else.


### Configuring Wireless Access Point
1. Make sure you have the `hostapd` and `dnsmasq` packages installed; refer to [Install Required Software/Packages](#packages) section
2. Configure a static IP address to the wireless interface by editing the `dhcpcd.conf` configuration file
	1. Edit `dhcpcd.conf`; enter `sudo vim /etc/dhcpcd.conf`
	2. Add the following lines to the end of the file:
		```
		interface wlan0
			static ip_address=192.168.2.1/24
			nohook wpa_supplicant
		```
	3. Restart the `dhcpcd` daemon; enter `sudo systemctl restart dhcpcd`
3. Configure the DHCP server by defining the content of `dnsmasq.conf`
	1. Rename the existing `dnsmasq.conf`; enter `sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig`
	2. Create a new/empty `dnsmasq.conf`; enter `sudo vim /etc/dnsmasq.conf`
	3. Add the following lines to the blank file:
		```
		interface=wlan0
		dhcp-range=192.168.2.2,192.168.2.20,255.255.255.0,24h
		```
	4. Restart `dnsmasq`; enter `sudo service dnsmasq restart`
4. Configure the wireless access point
	1. Edit `hostapd.confg`; enter `sudo vim /etc/hostapd/hostapd.conf`
	2. Replace any existing content with the follow lines:
		```
		interface=wlan0
		ssid=UAS_SAR_1
		hw_mode=g
		channel=6
		wmm_enabled=0
		wme_enabled=1
		macaddr_acl=0
		auth_algs=1
		ignore_broadcast_ssid=0
		wpa=2
		wpa_passphrase=BWSI_Rockx!1
		wpa_key_mgmt=WPA-PSK
		wpa_pairwise=TKIP
		rsn_pairwise=CCMP
		wpa_group_rekey=86400
		ieee80211n=1
		```
	3. Edit `hostapd`; enter `sudo vim /etc/default/hostapd`
	4. Find the line with `#DAEMON_CONF` and replace it with `DAEMON_CONF="/etc/hostapd/hostapd.conf"`
5. Start wireless access point
	1. Enable and start `hostapd` by entering:
	```
	sudo systemctl unmask hostapd
	sudo systemctl enable hostapd
	sudo systemctl start hostapd
	```
	2. Confirm wireless access point is running by using another wireless enabled machine to see if the `UAS_SAR_1` SSID is being broadcast
6. Adding routing and masquerading
	1. Open the following file and uncomment (delete the #) the following line:
		```
		sudo vim /etc/sysctl.conf
		net.ipv4.ip_forward=1
		```
	2. Add a masquerade for outbound traffic on eth0:
		```
		sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
        sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
		```
	3. Open the following file and add the following line just above "exit 0" to install these rules on boot.
		```
		sudo vim /etc/rc.local
		iptables-restore < /etc/iptables.ipv4.nat
	4. Using a wireless capable device, search for your network with the SSID you specified. The pi should now be broadcasting a wireless access point at 2.4GHz
7. Connect to the pi
	1. Congratulations! Your pi should now be able to be accessed wirelessly.
	2. Note: it may take a minute or two on boot for the pi to start broadcasting.
