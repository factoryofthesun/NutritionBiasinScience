cd "D:\GoogleDrive"
**************************************************************************************
*********READ IN AMAZON MTURK BATCH FILE - WHOLE GRAINS                      ********
**************************************************************************************
clear
*Without stripquotes, parts which have "sdasda" get strippedd off which makes AB no longer an identifier
import delimited using "Nutrition_BiasInScience\MTurk\wholegrains_batch_results.csv",  stripquotes(yes)
keep workerid worktimeinseconds inputtext answersentimentlabel

bysort inputtext: gen a = _n
egen worker_flag = group(workerid)
drop workerid

gen rating = 1 if answersentimentlabel =="Positive"
replace rating = -1 if answersentimentlabel =="Negative"
replace rating = 0 if answersentimentlabel =="Neutral"
replace rating = 99 if answersentimentlabel =="Unrelated"

*200 chars is a good lenght to maintain uniqueness
gen AB_clean = ustrregexra(inputtext,`"[^a-zA-Z0-9]"',"")
gen AB_trunc = substr(AB_clean, 1,200)
sort AB_trunc
drop answersentimentlabel inputtext

*One observation per abstract
reshape wide rating worktimeinseconds worker_flag , i(AB_trunc) j(a)
tempfile file1
save `file1'

clear
import delimited "Nutrition_BiasInScience\WebOfScience\Industry_Tagging\Outputs\wos_indtagged_final_wide.csv", delimiters(",") varnames(1)
gen AB_clean = ustrregexra(ab,`"[^a-zA-Z0-9]"',"")
gen AB_trunc = substr(AB_clean, 1,200)
sort AB_trunc
*There should be NO _merge=2
merge m:1 AB_trunc using  `file1'

keep if _merge==3
drop _merge
*Certain abstracts exist in multiple foodgroups - keep foodgroups of interest. Here whole grains excluding oats
destring foodcode is_industry_b2c, replace
keep if (foodcode<=22 & foodcode~=13)
save "Nutrition_BiasInScience\MTurk\wholegrains_batch_results_indtagged"

**************************************************************************************
*********INDUSTRY CODING AND RATINGS ACROSS 5 MTURK WORKERS        ********
**************************************************************************************
clear
use "Nutrition_BiasInScience\MTurk\wholegrains_batch_results_indtagged"
*append using "Nutrition_BiasInScience\MTurk\oats_batch_results_indtagged"

*Industry-funded or not? B2C or not?*********************************
gen ind_code = 1 if companies ~=""
replace ind_code = 0 if ind_code == .

gen ind_b2c_code = 1 if is_industry_b2c ~=0
replace ind_b2c_code = 0 if ind_b2c_code == .

*Ratings across 5 MTurk workers*********************************
 forvalues i = 1(1)5 {
 gen positive`i' = (rating`i'==1)  if  (rating`i'~=.)
 }
 forvalues i = 1(1)5 {
 gen unrelated`i' = (rating`i'==99|rating`i'==0)  if  (rating`i'~=.)
 }
 forvalues i = 1(1)5 {
 gen negative`i' = (rating`i'==-1)  if  (rating`i'~=.)
 }
 
 *Average ratings, -1, 0, 1: treating unrelated as 1) 0 or 2) missing
 forvalues i = 1(1)5 {
 gen rating`i'_unrelated0 = rating`i'*( rating`i'==1 | rating`i'==0 | rating`i'==-1) + 0 *(rating`i'==99)
 }
 forvalues i = 1(1)5 {
 gen rating`i'_unrelatedmissing = rating`i'*( rating`i'==1 | rating`i'==0 | rating`i'==-1) 
 replace rating`i'_unrelatedmissing = . if rating`i'==99
 }
 
egen avg_unrelated0 = rmean(rating1_unrelated0 rating2_unrelated0  rating3_unrelated0 rating4_unrelated0 rating5_unrelated0)
egen avg_unrelatedmissing = rmean(rating1_unrelatedmissing rating2_unrelatedmissing  rating3_unrelatedmissing rating4_unrelatedmissing rating5_unrelatedmissing)
egen majority = rsum(positive1 positive2  positive3 positive4 positive5)
gen majority_2 = majority>=2
gen majority_3 = majority>=3

egen majority_negative = rsum(negative1 negative2 negative3 negative4 negative5)
egen majority_unrelated = rsum(unrelated1 unrelated2 unrelated3 unrelated4 unrelated5)

*   Regressions: All vs related  ***********************************************************
reg majority_3 ind_code if !missing(ab)
reg majority_3 ind_code if !missing(ab) & (majority_negative>1 | majority>2)
reg avg_unrelated0 ind_code if !missing(ab)
reg avg_unrelatedmissing  ind_code if !missing(ab)

*With Fixed effects by food group
reghdfe majority_3 ind_code if !missing(ab) & (majority_negative>1 | majority>2), absorb(i.foodcode)
reghdfe avg_unrelated0  ind_code if !missing(ab), absorb(i.foodcode)
reghdfe avg_unrelatedmissing  ind_code if !missing(ab), absorb(i.foodcode)

*With industry effect by food group and fixed effects by food group
reghdfe majority_3 i1.ind_code#i.foodcode if !missing(ab), absorb(i.foodcode)
reghdfe majority_3 i1.ind_code#i.foodcode if !missing(ab) & (majority_negative>1 | majority>2), absorb(i.foodcode)
reghdfe avg_unrelated0  i1.ind_code#i.foodcode if !missing(ab), absorb(i.foodcode)
reghdfe avg_unrelatedmissing  i1.ind_code#i.foodcode if !missing(ab), absorb(i.foodcode)

*Control for other factors - year of publication, journal of publication, keywords
destring py, replace
egen so_numeric = group(so)
reghdfe avg_unrelated0  ind_code if !missing(ab), absorb(i.foodcode i.py i.so_num)
*Control for top 25 keywords----------------------------
gen id_clean = lower(ustrregexra(FU,`"[^a-zA-Z0-9;]"'," "))
gen id_1 = strpos(lower(id),"quality")>0
gen id_2 = strpos(lower(id),"starch")>0
gen id_3 = strpos(lower(id),"protein")>0
gen id_4 = strpos(lower(id),"dietarty fiber")>0
gen id_5 = strpos(lower(id),"products")>0
gen id_6 = strpos(lower(id),"wheat")>0
gen id_7 = strpos(lower(id),"flour")>0
gen id_8 = strpos(lower(id),"bread")>0
gen id_9 = strpos(lower(id),"temperature")>0
gen id_10 = strpos(lower(id),"fiber")>0
gen id_11 = strpos(lower(id),"performance")>0
gen id_12 = strpos(lower(id),"grain")>0
gen id_13 = strpos(lower(id),"barley")>0
gen id_14 = strpos(lower(id),"digestion")>0
gen id_15 = strpos(lower(id),"risk")>0
gen id_16 = strpos(lower(id),"consumption")>0
gen id_17 = strpos(lower(id),"physicochemical")>0
gen id_18 = strpos(lower(id),"proteins")>0
gen id_19 = strpos(lower(id),"acid")>0
gen id_20 = strpos(lower(id),"food")>0
gen id_21 = strpos(lower(id),"digestibility")>0
gen id_22 = strpos(lower(id),"gelatin")>0
gen id_23 = strpos(lower(id),"bran")>0
gen id_24 = strpos(lower(id),"gluten")>0
gen id_25 = strpos(lower(id),"endosperm")>0
reghdfe avg_unrelated0  ind_code if !missing(ab), absorb(i.foodcode i.id_*)
reghdfe avg_unrelated0  ind_code if !missing(ab), absorb(i.foodcode i.py i.so_num i.id_*)
teffects psmatch (avg_unrelated0) (ind_code i.id_* )
**************************************************************************************
*********SUMMARY STATISTICS - RATINGS, INDUSTRY FOR WHOLE GRAINS              ********
**************************************************************************************
summ avg_unrelated0 if !missing(ab) & foodcode ==13 & ind_code == 1
summ avg_unrelated0 if !missing(ab) & foodcode ==13 & ind_code == 0
summ avg_unrelated0 if !missing(ab) & foodcode !=13 & ind_code == 1
summ avg_unrelated0 if !missing(ab) & foodcode !=13 & ind_code == 0
 
bysort foodcode: summ avg_unrelated0 if !missing(ab) & ind_code==1
bysort foodcode: summ avg_unrelated0 if !missing(ab) & ind_code==0

**************************************************************************************
*********NEWS PAPER MENTIONS VS CITATIONS FOR WHOLE RGAINS********
**************************************************************************************

**************************************************************************************
*********	    READ AND CREATE MASTER FACTIVA DATA FILE	 						   ******
cd "Nutrition_BiasInScience\WebOfScience\Factiva_Data"
local foodcode "1 2 3 4 5 6 7 8 10 11 12 13 14 15 16 17 18 19 20 21 22"
foreach wg of local foodcode {
	xls2dta, save("G:\My Drive\Nutrition_BiasInScience\WebOfScience\Factiva_Data"): import excel "`wg'.xlsx", sheet("Sheet1") firstrow clear
	xls2dta: xeq rename search_terms ti
	xls2dta: xeq gen ti_trunc = substr(ti, 1,200)
	xls2dta: xeq rename number_of_results news_mentions
	xls2dta: xeq bysort ti: keep if _n==1
}

**Create an appended file with all Whole Grains (excluding oats - ase study)
clear
tempfile file2
save `file2', emptyok
cd "Nutrition_BiasInScience\WebOfScience\Factiva_Data"
local foodcode "1 2 3 4 5 6 7 8 10 11 12 13 14 15 16 17 18 19 20 21 22"
foreach wg of local foodcode {
     if `wg'==1 {
     gen foodcode = 1
     }
	append using "`wg'"
	replace foodcode = `wg' if foodcode==.
	save `file2', replace  
	}

*Verify if there are multiple titles under this - sometimes Factiva code writes wrong titles - and might happen----------
*bysort foodcode ti_trunc: gen flag=_n
*tab flag
*list ti if flag==2
*drop flag
rename id title_id
save "G:\My Drive\Nutrition_BiasInScience\WebOfScience\Factiva_Data\file2", replace	
**************************************************************************************

*********	   MERGE WITH INDUSTRY TAGGED WOS DATA						   ******
clear
import delimited "Nutrition_BiasInScience\WebOfScience\Industry_Tagging\Outputs\wos_indtagged_final_wide.csv",  varnames(1) encoding("utf-8") delimiters(",") bindquote(strict) 

gen ti_trunc = substr(ti, 1,200)
merge m:1 ti_trunc foodcode using "Nutrition_BiasInScience\WebOfScience\Factiva_Data\file2"

*There shouldnt be _merge = 1(except wheat) , ask RA to re-create these title if so. Currently 1 in wheat and 10 in oats(those 10 were not used in Mturk analysis)
list ti if _merge==1
list ti if _merge==2
drop if _merge==2 
*verify, then drop
drop if _merge == 1
drop _merge
*Drop non whole grains and oats
drop if foodcode>22 | foodcode==13
*If keeping oats in analysis - for summary stats
*drop if foodcode>22 
*****Check file for Davit - some that are _merge = 1 should be there**********
preserve
keep if _merge==1
keep foodcode foodname ti ab news_mentions duplicates_list titles info
export delimited davit_check.csv, replace
restore

*Industry-funded or not?*********************************
gen ind_code = 1 if companies ~=""
replace ind_code = 0 if ind_code == .

destring py, replace
egen so_numeric = group(so)

*drop if news_mentions>50 & news_mentions~=.
*Exclude outlier news mentions, happens with books or titles like "Oat"
*Exclude those with missing abstracts, to be consistent with positive/negative analysis
*ttest news_mentions if !missing(ab) & !(news_mentions>50 & news_mentions~=.), by(ind_code)
*ttest news_mentions if !(news_mentions>50 & news_mentions~=.), by(ind_code)

*0-1 coding to see if it gets a news mention or not, not the intensity of it
gen news_mentions_01 = (news_mentions>0 & news_mentions~=. & news_mentions<=50)
reg news_mentions_01 ind_code if !missing(ab) &  !(news_mentions>50 & news_mentions~=.)
reghdfe news_mentions_01 ind_code if !missing(ab) &  !(news_mentions>50 & news_mentions~=.), absorb(i.foodcode)
reghdfe news_mentions_01 ind_code if !missing(ab) &  !(news_mentions>50 & news_mentions~=.), absorb(i.foodcode i.py)
reghdfe news_mentions_01 ind_code if !missing(ab) &  !(news_mentions>50 & news_mentions~=.), absorb(i.foodcode i.py i.so_num)
reghdfe news_mentions_01 ind_code if !missing(ab) &  !(news_mentions>50 & news_mentions~=.), absorb(i.foodcode i.py i.so_num i.id_*)

reg tc ind_code if !missing(ab) &  !(news_mentions>50 & news_mentions~=.)
reghdfe tc ind_code if !missing(ab) &  !(news_mentions>50 & news_mentions~=.), absorb(i.foodcode)
reghdfe tc ind_code if !missing(ab) &  !(news_mentions>50 & news_mentions~=.), absorb(i.foodcode i.py)
reghdfe tc ind_code if !missing(ab) &  !(news_mentions>50 & news_mentions~=.), absorb(i.foodcode i.py i.so_num)
reghdfe tc ind_code if !missing(ab) &  !(news_mentions>50 & news_mentions~=.), absorb(i.foodcode i.py i.so_num i.id_*)

reghdfe news_mentions_01 i1.ind_code#i.foodcode if !missing(ab) &  !(news_mentions>50 & news_mentions~=.), absorb(i.foodcode)
reghdfe tc i1.ind_code#i.foodcode if !missing(ab) &  !(news_mentions>50 & news_mentions~=.), absorb(i.foodcode)

reg news_mentions ind_code if !missing(ab) &  !(news_mentions>50 & news_mentions~=.)

**************************************************************************************
*********SUMMARY STATISTICS - RATINGS, INDUSTRY FOR WHOLE GRAINS              ********
**************************************************************************************
summ news_mentions_01 if !missing(ab) & foodcode ==13 & ind_code == 1
summ news_mentions_01 if !missing(ab) & foodcode ==13 & ind_code == 0
summ news_mentions_01 if !missing(ab) & foodcode !=13 & ind_code == 1
summ news_mentions_01 if !missing(ab) & foodcode !=13 & ind_code == 0

summ tc if !missing(ab) & foodcode ==13 & ind_code == 1
summ tc if !missing(ab) & foodcode ==13 & ind_code == 0
summ tc if !missing(ab) & foodcode !=13 & ind_code == 1
summ tc if !missing(ab) & foodcode !=13 & ind_code == 0
