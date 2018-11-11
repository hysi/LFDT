# -*- coding: UTF-8 -*-

# To generate the random examples, ie., (I,J)s, from 
# a normal logic program P by choose a dynamic update

# To run as follows:
# <this-file> <program> <num_of_Is> <num_of_Js> (the number of Js for each I)

# Written by Yisong Wang
# 2017.11.30
import pdb
import numpy as np
import math        # for ceil function
import os          # for file reading and writting
import sys, getopt # for argv argument

atoms= list()

atom_names={'1', 'b'}

class cRule:
      head=0
      pos=list()
      neg=list()
      # checking if the body is satisfied by an interpretation interp 
      # represented in set
      def satisfy_body(self, interp):
         for m in self.pos:
            if not m in interp:
               return False
         for m in self.neg:
            if m in interp:
               return False
         return True

      def print(self):
         lenp = len(self.pos)
         lenn = len(self.neg)
         print("%d "%self.head, end='')
         # print positive body
         if lenp + lenn > 0: print(":- ",end='')
         for i in range(0,lenp,1):
           print("%d"%self.pos[i], end='')
           if i < lenp-1: print(", ",end='')

         # print negative body
         if lenp > 0 and lenn > 0: print(", ", end='')
         for j in range(0,lenn):
           print("-%d"%self.neg[j], end='')
           if j < lenn-1: print(", ",end='')

      # deciding if an interpretation satisfies the rule
      def satisfy(self, interpretation):
         if satisfy_body(interpretation):
            if not  self.head in interprettion:
               return False
         return True

      # to build the rule from a given string in rule format
      def __init__(self, rule_str):
         self.head = 0
         self.pos = list()
         self.neg = list()
         [h,b]=rule_str.split(":-")		
         self.head=int(h)
         if b.count(',') > 0:
          lb = b.split(',')
          lbint = list(map(int, lb))
         else:
          lbint = [int(b)]
         for atom in lbint:
            if atom > 0: 
              self.pos.append(atom)
            if atom < 0:
              self.neg.append(abs(atom))

class cNLP:
      num_of_atoms = 0
      num_of_rules = 0
      Rules = []
      Atoms = set()
      UpdateProbability = []
      # to kep the Is
      RandomIs=[]

      def print(self):
        lr = len(self.Rules)
        for i in range(0,lr):
          self.Rules[i].print()
          if i < lr: print("")

      # get the set of atoms from an interpretation in  integer representation 
      def getAtoms(self, atom, base=10):
        s = set()
        for i in range(1,base+1):
          if  atom & 0x1 == 1:
            s.add(i)
          atom = atom >> 1
        return s

      # deciding if the set J1 is a subset of J2 that are represented in integers 
      def subset(self,J1,J2):
        if J1 & J2 == J1:
          return True
        else:
          return False

      # compute the number bodies that are satisfied by an interpretation I
      # which is represented in set
      def satisfied_bodys(self, Inp):
        s = 0
        sat_heads = set()
        for rule in self.Rules:
          if rule.head in sat_heads: continue
          if rule.satisfy_body(Inp): 
            s = s+1
            sat_heads.add(rule.head)
        return s

      # deciding if the status of the 'atom' will never be changed in terms of 'I'
      def atom_no_change(self,atom,I):
        intp = self.getAtoms(I)
        #update to True, some rule body with its head is the atommis satisfied
        update_True = False 
        #update to False, i.e, no rule body with its head is the atom is satisfied
        #update_False = True 
        for rule in self.Rules:
          if rule.head != atom: continue
          if rule.satisfy_body(intp): 
            update_True = True
            break
        if update_True and not atom in intp: return False # change to be true
        if not update_True and atom in intp: return False # change to be false
        return True
        '''if (update_True and atom in intp) or (update_False and not atom in intp):
          return True
        else:
          return False
        '''

      # get the unchange atoms for a given interpretation in integer
      # I.e, the satus of the atom is unchanged no matter change or
      # do not change its status
      def unchange_atoms(self, I):
        unchange = set() 
        intp = self.getAtoms(I)
        for atom in self.Atoms:
          if self.atom_no_change(atom, I): 
            unchange.add(atom)
        return unchange
      
      # compute c(n,m)
      def combination(self,n,m):
        s=1
        t=1
        for i in range(1,n-m+1):
          s = s*i
        for j in range(m+1,n+1):
          t = t*j
        return t/s

      # generate random I for the <I,J> examples which guarantee that
      # at least k different rules' body are satisfied
      def genRandomIs(self, num_of_Is, num_of_Js):
        self.RandomIs = list()
        na = len(self.Atoms)
        # the least number of satisfied bodies for number of minimal
        # Js under set inclusion 
        # the condition is: 2 ** n >= num_of_Js
        nr = 1
        while (self.combination(nr,math.ceil(nr/2)) < num_of_Js): 
          nr = nr+1
        ImpossibleIs=set()
        s = 0
        while (s < num_of_Is):
          if len(ImpossibleIs) + s == 2**na: 
            print("There is no sufficient examples for %d Is and %d Js!"\
             %(num_of_Is,num_of_Js))
            sys.exit(0)
          I = np.random.random_integers(1,2**len(self.Atoms))
          if I in self.RandomIs or I in ImpossibleIs: continue
          unchange = self.unchange_atoms(I)
          if len(self.Atoms)-len(unchange) < nr: 
            ImpossibleIs.add(I)
            continue
          self.RandomIs.append(I)
          s = s + 1

      # generate k minimal Js as <I,J1>,...,<I,Jk>
      # I is an set of atoms represented by an integer
      def genJs(self, I, k):
        si = self.getAtoms(I)
        fixed = self.unchange_atoms(I)
        change = self.Atoms.difference(fixed)
        len_change = len(change)
        Js = list()
        while(True):
          # generate k different random integers that
          # represent k sets
          Js = set(np.random.random_integers(0,2**len_change-1,(k,)))
          while(len(Js) < k):
            it = np.random.random_integers(1,2**len_change-1)
            if it in Js: continue
            Js.add(it)
          # checking if the k sets are minimal under set inclusion
          Js = list(Js)
          i = 0
          while(i<k-1):
            j = i+1
            while (j<k):
              if self.subset(Js[i],Js[j]): break 
              if self.subset(Js[j],Js[i]): break
              j = j+1
            if j < k: break
            i = i+1
          if i<k-1: continue
          else: break # these k sets are minimal under set inclusion
        #end of while(True)      
        change_list = list(change)
        JsList = list()
        # build up the Js for I as examples <I,J1>,...
        for J in Js:
          Jtemp = list()
          J_index = self.getAtoms(J,len_change)
          for ind in J_index:
            Jtemp.append(change_list[ind-1])
          for at in fixed.intersection(si): 
          # add the true atoms that are unchanged
            Jtemp.append(at)
          JsList.append(Jtemp)
        return JsList

      # update the probability
      def ChangeUpdateProbability(self, prob):
        self.UpdateProbability = prob
      
      # read the normal logic program from the nlp_file 
      def __init__(self, nlp_file):
        global atoms
        global atom_names

        fp = open(nlp_file)
        line = fp.readline()
        while(line != ''):
          line.strip() # remove the left and right blanks
          #--orginal code  begin
          #if line == '' or line.startswith('#'):
           # line = fp.readline()
            #continue
          #--orginal code end
          #-----The following code is add by Yi 2018-11-08
          if line == '':
              line = fp.readline()
              continue
          if line.startswith('#'):
              line = line.lstrip('#').lstrip().rstrip('\n')
              line1 = line.replace(',','')
              if line1.isdigit():
                atoms_str = line.split(',')
                atoms_list = list(map(lambda  x: int(x), atoms_str))
                atoms=set(atoms_list)
              else:
                atom_names = line.split(',')
              line = fp.readline()
              continue;
          #---------end------yi 20181108
          rule = cRule(line)
          self.Rules.append(rule)
          self.num_of_rules += 1
          line = fp.readline()
        # end of while
        fp.close()      
        # build up the atoms
        self.Atoms = atoms
        # set the update probability of atoms  0.5 by default
        self.UpdateProbability = len(self.Atoms) * [0.5]


if __name__=="__main__":
    if len(sys.argv) != 4:
       print("Usage: %s <NLP> <Num_of_Is> <num_of_Js for each I>"%argv[0])
       sys.exit(main())
    NLP = cNLP(sys.argv[1])
    num_of_atoms = len(atoms)
    num_of_Is= int(sys.argv[2])
    num_of_Js = int(sys.argv[3]) 
   
    # print the first line of the example file
    # atom_names=['CycD','Rb','CycE','CycA','CycB','p27','E2F','Cdc20','Cdh1','Ubch10']
    for n in atom_names:
      print(n,end='')
      #------original code---------
      #if n != 'Ubch10': print(',',end='')
      #----new code add by yi huang 20181108
      if n != atom_names[-1]: print(',',end='')
      #----new code end-----------------------
    print("")
    # generate the random <I,J> examples
    NLP.genRandomIs(num_of_Is,num_of_Js)
    #RandomIs = np.random.random_integers(1,2**num_of_atoms,(num_of_Is,))
    for I in NLP.RandomIs:
      Js = NLP.genJs(I,num_of_Js)
      # print this <I,J>s in an ugly REQUIRED format
      for s in Js:
        # print I
        sa = NLP.getAtoms(I)
        for atom in sa: print(atom_names[atom-1],end='')
        print(">",end='')
        for atom in s:  print(atom_names[atom-1],end='')
        print("")
    # end of __main__
