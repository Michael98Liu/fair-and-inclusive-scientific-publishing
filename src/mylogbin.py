import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from sys import argv

#  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #

def mylogbin (y,base):

	y.sort()

	ymax = y[-1]
	nsum = len(y)

	x = [1]
	i = 1
	while True:
		n = int(np.power(base,i))
		if x[-1] != n: # to avoid repeated bins (only in the beginning of x for small bases)
			x.append(n)
		if n > ymax:
			break
		i += 1

	h = np.zeros_like(x,dtype=np.double)
	x0 = np.zeros_like(x,dtype=np.double)
	i = 0
	for n in y:
		while x[i] < n:
			if i < 1:
				norm = nsum
				x0[i] = 1
			else:
				norm = nsum * (x[i] - x[i - 1])
				x0[i] = 0.5 * (x[i] + x[i - 1] + 1)
			h[i] /= norm # dividing by the width of the histogram
			i += 1 # incrementing
		h[i] += 1

	h[-1] /= nsum * (x[-1] - x[-2])
	x0[-1] = 0.5 * (x[-1] + x[-2] + 1)

	lx = []
	ly = []

	for i in range(len(h)):
		if h[i] > 1.0e-15:
			lx.append(x0[i])
			ly.append(h[i])

	return lx,ly

#  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #

def f (x,a,b,c):
	#return a*np.exp(-b*np.power(x,c))
	return np.log(a*np.exp(-b*np.exp(x*c)))

#  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #

def fit_se (x,y):

	lx = np.log(x)
	ly = np.log(y)

	lx0 = min(lx)
	lx1 = 1.1*max(lx)

	popt, pcov = curve_fit(f, lx, ly, p0=[2,3,0.1], bounds=([0,0,0],[np.inf,np.inf,1]))

	print(popt)

	x = np.linspace(lx0,lx1,500)
	y = [f(xx,*popt) for xx in x]

	return np.exp(x),np.exp(y)

#  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #  #

if __name__ == "__main__":
	
	if len(argv) != 2:
		print('usage: python3 logbin.py [base]')
		exit()

	s = pd.read_csv('./AllEditorSampledAuthor.csv',sep='\t', usecols=['NewAuthorId','Yfp','Aylp','Parent','EditorsNewId','issn','Year0','Eylp','APriorPaperCount','EPriorPaperCount','APriorCitationCount','EPriorCitationCount','Arank','Erank'],dtype={'NewAuthorId':int,'Yfp':int,'Aylp':int,'Parent':int,'EditorsNewId':int,'issn':str,'Year0':int,'Eylp':int,'APriorPaperCount':int,'EPriorPaperCount':int,'APriorCitationCount':int,'EPriorCitationCount':int,'Aage':int,'Eage':int,'Arank':int,'Erank':int})

	base = float(argv[1])
	assert(base > 1.0)

	plt.xscale('log')
	plt.yscale('log')
	a = s['APriorPaperCount'].to_numpy()
	x, h = mylogbin(a,base)
	print('APriorPaperCount',max(a),len(a))
	plt.plot(x,h,marker='X',ls='None')
	x,y = fit_se(x,h)
	plt.plot(x,y)
	a = s['EPriorPaperCount'].to_numpy()
	x, h = mylogbin(a,base)
	print('EPriorPaperCount',max(a),len(a))
	plt.plot(x,h,marker='o',ls='None')
	x,y = fit_se(x,h)
	plt.plot(x,y)
	plt.savefig('papercount.pdf')
	plt.close()

	plt.xscale('log')
	plt.yscale('log')
	a = s['APriorCitationCount'].to_numpy()
	print('APriorCitationCount',max(a),len(a))
	x, h = mylogbin(a,base)
	plt.plot(x,h,marker='X',ls='None')
	x,y = fit_se(x,h)
	plt.plot(x,y)
	a = s['EPriorCitationCount'].to_numpy()
	print('EPriorCitationCount',max(a),len(a))
	x, h = mylogbin(a,base)
	plt.plot(x,h,marker='o',ls='None')
	x,y = fit_se(x,h)
	plt.plot(x,y)
	plt.savefig('citationcount.pdf')
	plt.close()
