**************************************************************************************
*#Step 1. Read downloaded abstract files into Stata***********************************
*#Notes: Unique identifiers title, and YofPub (some titles are repeated likely because published in another journal)
*TC: citation count, FU: funding agency, AB abstract, TI: title

local files : dir "D:\Dropbox\Nutrition_BiasInScience\WebOfScience\Food&Nutrition" files "*.xlsx"
cd "D:\Dropbox\Nutrition_BiasInScience\WebOfScience\Food&Nutrition"

*Use end in command prompt to continue for loop, after verifying FU is correct
pause on
foreach file in `files' {
disp "`file'"
*import delimited 23.txt, delimiters(tab) varnames(1) encoding ("utf-16")
import excel `file', sheet("1") firstrow clear

**************************************************************************************
*#Step 2. Code in industry names for funding agencies*********************************
*#Make funding name generic - remove special characters and add spaces so co is different from mexico
gen FU_clean = ustrregexra(FU,`"[^a-zA-Z0-9]"'," ")
replace FU_clean = " " + FU_clean + " "

*#2a.Generic industry identifiers
gen ind1 = 0
local generic_ind_list "" ltd " " limited " " company " " plc " " inc " " co " " llc " " incorporated " " ltda " " spa " " gmbh ""
foreach var of local generic_ind_list {
disp "`var'"
replace ind1 = 1 if strpos(lower(FU_clean),"`var'")>0
}

*#2b.Top 100 industry identifiers - manually created from industry top 100 list
preserve

clear
import excel "D:\Dropbox\Nutrition_BiasInScience\WebOfScience\Industry Names\FP2019-Top100sort.xls", sheet("Sheet2") firstrow clear
levelsof name_clean, local(top100_ind_list)

restore

*#Exclude contains those names that get convoluted with the name_clean. For e.g, Post is a top 100 firm, but this means post doctoral gets included. Need to exclude those instances
preserve
clear
import excel "D:\Dropbox\Nutrition_BiasInScience\WebOfScience\Industry Names\FP2019-Top100sort.xls", sheet("exclude") firstrow clear
levelsof name_exclude, local(instances_to_exclude)
restore

gen ind2 = 0
gen ind_string = ""
foreach var of local top100_ind_list {
disp "`var'"
replace ind2 = 	1 if strpos(lower(FU_clean),"`var'")>0
*Use this for checking if company names make sese. E.g. postgraduate for post is not included
replace ind_string = substr(FU_clean,strpos(lower(FU_clean),"`var'"),10) if strpos(lower(FU_clean),"`var'")>0
}

gen not_ind = 0
foreach var of local instances_to_exclude {
disp "`var'"
replace not_ind = 1 if strpos(lower(FU_clean),"`var'")>0
}

*See if these names make sense
list FU if ind2==1
*See if this is the right set to exclude
list FU if not_ind==1
tab ind_string if ind1==1

gen     ind = 0 
replace ind=1 if (ind1==1 | (ind2==1 & not_ind==0))


pause
}

**NOTES: NEED TO REMOVE CO ORDINATED, GETS CODED AS CO INTO IND1, All India Co Ordinated Small Millets Improvement Project  AlCSMIP  
**quinoa, need to exclude Universidad Nacional de Juliaca  UNAJ  from the Canon Minero Project 2013  Puno  Peru  086 2013 CO UNAJ
**triticale: need to remove Value Added Wheat Co operative Research Centre
**************************************************************************************
#Step 3. Analyze citations by industry, non-industry**********************************
ttest TC, by(ind)

#Step 4. Merge in factiva news database. Once this is done and file saved, no need to redo
***preserve
***
***clear
***import excel "D:\Dropbox\Nutrition_BiasInScience\WebOfScience\Factiva database\oats_factiva.xlsx", sheet("Sheet1") firstrow clear
***rename AbstractTitle TI
***rename NumberofResults news_mentions
***sort TI
***bysort TI: keep if _n==1
***save "D:\Dropbox\Nutrition_BiasInScience\WebOfScience\Factiva database\oats_factiva", replace
***
***restore

merge m:1 TI using "D:\Dropbox\Nutrition_BiasInScience\WebOfScience\Factiva database\oats_factiva"
list TI if _merge==1
list TI if _merge==2
drop _merge

******************************************************************************************
#Step 5. Merge in  abstract positive/negative*********************************************           
*Once this is done and file saved, no need to redo        
***preserve
***
***clear
****Without stripquotes, parts which have "sdasda" get strippedd off which makes AB no longer an identifier
***import delimited using "D:\Dropbox\Nutrition_BiasInScience\WebOfScience\1.Oats\Batch_3892571_batch_results.csv",  stripquotes(yes)
***keep workerid worktimeinseconds inputtext answersentimentlabel
***
***bysort inputtext: gen a = _n
***egen worker_flag = group(workerid)
***drop workerid
***
***gen rating = 1 if answersentimentlabel =="Positive"
***replace rating = -1 if answersentimentlabel =="Negative"
***replace rating = 0 if answersentimentlabel =="Neutral"
***replace rating = 99 if answersentimentlabel =="Unrelated"
***
****200 chars is a good lenght to maintain uniqueness
***gen AB_clean = ustrregexra(inputtext,`"[^a-zA-Z0-9]"',"")
***gen AB_trunc = substr(AB_clean, 1,200)
***sort AB_trunc
***drop answersentimentlabel inputtext
***
****One observation per abstract
***reshape wide rating worktimeinseconds worker_flag , i(AB_trunc) j(a)
***save "D:\Dropbox\Nutrition_BiasInScience\WebOfScience\1.Oats\Batch_3892571_batch_results_reshaped",replace
***
***restore 

*Need to do in two steps, because when i import mturk batch file I strip out the "" - sp the abstracts wont match unless this is done in two steps.
gen AB_clean = ustrregexra(AB,`"[^a-zA-Z0-9]"',"")
gen AB_trunc = substr(AB_clean, 1,200)
sort AB_trunc
*There should be NO _merge=2
merge m:1 AB_trunc using "D:\Dropbox\Nutrition_BiasInScience\WebOfScience\1.Oats\Batch_3892571_batch_results_reshaped"

forvalues i = 1(1)5 {
 gen positive`i' = (rating`i'==1)
 }

egen avg = rmean(positive1 positive2  positive3 positive4 positive5)

reg avg ind if !missing(AB)
ttest avg if !missing(AB), by (ind)


*drop if news_mentions>50 & news_mentions~=.
*Exclude outlier news mentions, happens with books or titles like "Oat"
*Exclude those with missing abstracts, to be consistent with positive/negative analysis
ttest news_mentions if !missing(AB) & !(news_mentions>50 & news_mentions~=.), by(ind)
ttest news_mentions if !(news_mentions>50 & news_mentions~=.), by(ind)

*0-1 coding to see if it gets a news mention or not, not the intensity of it
gen news_mentions_01 = (news_mentions>0 & news_mentions~=. & news_mentions<=50)
reg news_mentions_01 ind