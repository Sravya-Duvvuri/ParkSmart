show databases;
use my_app_db;
show tables;
select * from tbl_admins;
select * from tbl_users;
select * from payments;
select * from tbl_vehicles;
select * from tbl_wallets;
select * from tbl_credit_transactions;
select * from tbl_debit_transactions;	
select * from tbl_transactions;
select * from tbl_upi_transactions;

SELECT transaction_id, user_email, start_time, amount, status FROM tbl_transactions;

drop table tbl_vehicles;
drop table tbl_wallets;