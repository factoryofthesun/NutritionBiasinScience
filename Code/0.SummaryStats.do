***********OVERALL STATISTICS ON RATINGS, CITATIONS PER GRAIN***************
clear
use "Nutrition_BiasInScience\MTurk\wholegrains_batch_results_indtagged"
append using "Nutrition_BiasInScience\MTurk\oats_batch_results_indtagged"


clear
import delimited "D:\GoogleDrive\Nutrition_BiasInScience\WebOfScience\Industry_Tagging\Outputs\wos_indtagged_final_wide.csv", delimiters(",") varnames(1)

gen ind_code = 1 if companies~=""
replace ind_code = 0 if ind_code== .

*1.keywords-----------------------------------------------------------------------------------
*****Do industry titles differ from non-industry in terms of keywords, journal of publication?
keep foodcode ind_code ti sc so de id
*IF looking only at wholegrains---------------------------------------------
drop if strpos(foodcode,";")>0
destring foodcode, replace
keep if foodcode<=22

*FIND TOP AUTHOR KEYWORDS ACROSS ALL FOODGROUPS------------------------------
*Notes: trailing spaces are not deleted. So you will have oat and _oat as two entries. Ignored for now
*tab de if de=="", m
gen de_clean = lower(ustrregexra(de,`"[^a-zA-Z0-9;]"'," "))
split de_clean, parse(;)
drop de de_clean
keep foodcode ind_code ti sc so de*
bysort ti: keep if _n==1
reshape long de_clean, i(foodcode ind_code ti sc so) j(keyword)

*Remove trailing and leading blanks
replace de_clean = strtrim(de_clean )
drop if de_clean == ""

egen de_group = group(de_clean)

    *Stat1: Are there keywords where there is NO non-industry article? ALmost never----------
forvalues i = 1(1)8 {
*forvalues i = 11(1)22 {
    preserve
    keep if foodcode == `i'
    *keep if foodcode == `i' & strpos(lower(sc),"nutrition")
    
    bysort de_clean: gen count=_N
    drop if count<=2
    bysort de_clean: egen count_ind = sum(ind)
    disp("`i'")
    gen count_nonind = count_ind -count
    *tab de_clean if count_nonind ==0
    restore
}

*Stat2: Are there journals where there is NO non-industry article?
forvalues i = 1(1)8 {
*forvalues i = 11(1)22 {
    preserve
    keep if foodcode == `i'
    *keep if foodcode == `i' & strpos(lower(sc),"nutrition")
    
    bysort so: gen count_so = _N
    drop if count<=2
    bysort so: egen count_so_ind = sum(ind)
    disp("`i'")
    gen count_so_nonind = count_so_ind-count_so
    tab so if count_so_nonind==0
    
    restore
}
    
    
    *What are the top 10 keywords in that foodcode?----------------------
    *bysort de_clean: keep if _n==1
    *gsort -count
    *list de_clean count if _n<=10
    
    *Are industry funded articles in certain keywords?--------------------
    *foreach var in "amaranth" "amaranth proteins" "amaranth flour" "antioxidant activity" "rheology" "starch" "functional properties" "amaranth oil" "germination" "grain amaranth" {
     foreach var in "barley" "beta glucan" "malt" "malting" "starch" "germination" "malting quality" "hull less barley" "antioxidant activity" "beta glucans" {
		*foreach var in "resitant starch" "anthocyanins" "biofortification" "antioxidant activity" {
		 	gen dep_var = (de_clean == "`var'")
		  reg dep_var ind_code
		  drop dep_var
		  }
	  restore
}

bysort de_clean: gen count_de = _N
bysort de_clean ind_code: gen count_de_ind = _N
bysort de_clean ind_code: keep if _n==1

gsort ind_code -count_de_ind
br

*FIND TOP KEYWORDS PLUS ACROSS ALL FOODGROUPS------------------------------
gen id_clean = lower(ustrregexra(id,`"[^a-zA-Z0-9;]"'," "))
split id_clean, parse(;)
drop id id_clean
keep foodcode ind_code ti id*
bysort ti: keep if _n==1
reshape long id_clean, i(foodcode ind_code ti) j(keyword)

drop if id_clean == ""
bysort id_clean: gen count_id = _N
bysort id_clean ind_code: gen count_id_ind = _N
bysort id_clean ind_code: keep if _n==1

gsort ind_code -count_id_ind
br

***--------------------------------------------------------------------------------------------------
*2.year of publication, py and journal of publication, so--------------------------------------------
drop if strpos(foodcode,";")
destring foodcode, replace
keep if foodcode <=22

destring py, replace
reg py ind_code
*Industry funded articles are more recent, by 11 years: 2013, suggesting this is since the advent of "marketing"

egen so_num = group(so)
set matsize 10000
reghdfe ind_code i.so_num, noabsorb
*Some journals have higher likelihood of seeing ind publications
