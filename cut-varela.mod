# FROM "AMPL - A MODELING LANGUAGE FOR MATHEMATICAL PROGRAMMING", 2ND ED, by Fourer, Gay, and Kernighan.
# Section 14.4

# Data specification
param roll_width > 0;

set WIDTHS; # set of widths to be cut
param orders {WIDTHS} > 0; # number of each width to be cut

param nPAT integer >= 0; # number of patterns
set PATTERNS = 1..nPAT; # set of patterns

param nbr {WIDTHS,PATTERNS} integer >= 0;
	check {j in PATTERNS}:
		sum {i in WIDTHS} i * nbr[i,j] <= roll_width; # defn of patterns: nbr[i,j] = number of rolls of width i in pattern j

# Cutting_Opt problem
var Cut {PATTERNS} integer >= 0; # rolls cut using each pattern

minimize Number: # minimize total raw rolls cut
	sum {j in PATTERNS} Cut[j];

subject to Fill {i in WIDTHS}: # for each width, total rolls cut meets total demand
	sum {j in PATTERNS} nbr[i,j] * Cut[j] >= orders[i]; # CONSIDER REPLACING BY EQUALITY CONSTRAINT?

# Pattern_Gen problem
param price {WIDTHS} default 0.0; # prices from cutting opt

var Use {WIDTHS} integer >= 0; # numbers of each width in pattern

minimize Reduced_Cost:
	1 - sum {i in WIDTHS} price[i] * Use[i];

subject to Width_Limit:
	sum {i in WIDTHS} i * Use[i] <= roll_width;