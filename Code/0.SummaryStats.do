*****Do industry titles differ from non-industry in terms of keywords, journal of publication?
clear
import delimited "G:\My Drive\Nutrition_BiasInScience\WebOfScience\Industry_Tagging\Outputs\wos_indtagged_final_wide.csv", delimiters(",") varnames(1)

gen ind_code = 1 if companies~=""
replace ind_code = 0 if ind_code== .

keep foodcode ind_code ti de id
*IF looking only at wholegrains---------------------------------------------
drop if strpos(foodcode,";")>0
destring foodcode, replace
keep if foodcode<=22

*FIND TOP AUTHOR KEYWORDS ACROSS ALL FOODGROUPS------------------------------
gen de_clean = lower(ustrregexra(de,`"[^a-zA-Z0-9;]"'," "))
split de_clean, parse(;)
drop de de_clean
keep foodcode ind_code ti de*
bysort ti: keep if _n==1
reshape long de_clean, i(foodcode ind_code ti) j(keyword)

drop if de_clean == ""
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



