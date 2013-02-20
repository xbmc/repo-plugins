
/* show date of first record in api_apilog	*/
select user_id, email, min(inserted) from api_apilog left join auth_user as AU on AU.id=user_id group by user_id, email order by min(inserted);

/* the same, sort by new users */
select user_id, email, min(inserted), date_joined from api_apilog left join auth_user as AU on AU.id=user_id group by user_id, date_joined, email order by min(date_joined) desc;

/* api users with api request counts */
select user_id, email, min(inserted), date_joined from api_apilog left join auth_user as AU on AU.id=user_id group by user_id, date_joined, email order by min(date_joined) desc;

/* checkins whith software info filled-in	*/
select * from actions_checkin where data like '%software_info":"{%' and data!='{}' and data!='';
