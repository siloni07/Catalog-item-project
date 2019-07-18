# ITEM CATALOG
Item Catalog is a flask-sqlalchemy based web application which has different sports equipment details under sports catalog where only authenticated and authorized users can create,edit and delete the items.

## Quick Installation
Virtual Machine Installation :- Clone the project [here](https://github.com/siloni07/Catalog-item-project) Install Vagrant[here](https://www.vagrantup.com/downloads.html) and Virtual Machine[here](https://www.oracle.com/technetwork/server-storage/virtualbox/downloads/index.html) set-up In Git Bash run the following command to make your virtual machine up and running.

```
cd catalog/
vagrant up
```
Please note it may take sometime for "vagrant up" command to get complete. Now, The system is ready to use. Use _Vagrant ssh_ command afterwards to fastly configure your virtual machine.

## Install
* Execute the following command to get pre-requisite data in database:-
```
python catalogrecords.py
```
* Execute following command to bring server up and running
```
python project.py
```
* Use Chrome or Firefox to render website (http://localhost:8071/)  .Once your website is rendered. You can view different sports categories by clicking on sport's name. You need to login using _click here to login_ button on top rightmost corner. Once authenticated using gmail sign-on,one can create,update,delete various sports items.
* All the latest menu items which will be added into the website will start coming under *Latest Menu Items* slab.