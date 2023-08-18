import numpy as np


class LEFTranslocator():
    
    def __init__(self,
                 numLEF,
                 deathProb,
                 stalledDeathProb,
                 birthArray,
                 pauseProb,
                 stallProbLeft,
                 stallProbRight,
                 *args):
    
        self.numSite = len(birthArray)
        self.numLEF = numLEF
        
        self.stallProbLeft = stallProbLeft
        self.stallProbRight = stallProbRight
        
        self.deathProb = deathProb
        self.pause = pauseProb
        
        birthArray[0] = 0
        birthArray[-1] = 0
        
        self.birthProb = np.cumsum(birthArray, dtype=np.double)
        self.birthProb /= self.birthProb[-1]
        
        self.LEFs = np.zeros((self.numLEF, 2), int)
        self.stalled = np.zeros((self.numLEF, 2), int)
        
        self.occupied = np.zeros(self.numSite, int)
        self.stalledDeathProb = stalledDeathProb
        
        self.occupied[0] = 1
        self.occupied[-1] = 1

        for i in range(self.numLEF):
            self.LEF_birth(i)


    def LEF_birth(self, i):
    
        while True:
            pos = np.searchsorted(self.birthProb, np.random.random())
            
            if pos >= self.numSite - 1:
                print("bad value", pos, self.birthProb[len(self.birthProb)-1])
                continue
                
            if pos <= 0:
                print("bad value", pos, self.birthProb[0])
                continue 
 
            if self.occupied[pos] == 1:
                continue
            
            self.LEFs[i] = pos
            self.occupied[pos] = 1
            
            if (pos < (self.numSite - 3)) and (self.occupied[pos+1] == 0):
                if np.random.random() > 0.5:
                    self.LEFs[i, 1] = pos + 1
                    self.occupied[pos+1] = 1
            
            return


    def LEF_death(self):
    
        for i in range(self.numLEF):
            if self.stalled[i, 0] == 0:
                deathProb1 = self.deathProb[self.LEFs[i, 0]]
            else: 
                deathProb1 = self.stalledDeathProb[self.LEFs[i, 0]]
                
            if self.stalled[i, 1] == 0:
                deathProb2 = self.deathProb[self.LEFs[i, 1]]
            else:
                deathProb2 = self.stalledDeathProb[self.LEFs[i, 1]]
            
            deathProb = max(deathProb1, deathProb2)
            
            if np.random.random() < deathProb:
                self.occupied[self.LEFs[i, 0]] = 0
                self.occupied[self.LEFs[i, 1]] = 0
                
                self.stalled[i] = 0
                self.LEF_birth(i)
        

    def LEF_step(self):
    
        for i in range(self.numLEF):            
            stall1 = self.stallProbLeft[self.LEFs[i, 0]]
            stall2 = self.stallProbRight[self.LEFs[i, 1]]
                                    
            if np.random.random() < stall1:
                self.stalled[i, 0] = 1
                
            if np.random.random() < stall2:
                self.stalled[i, 1] = 1
                         
            cur1, cur2 = self.LEFs[i]
            
            if self.stalled[i, 0] == 0:
                if self.occupied[cur1-1] == 0:
                    pause1 = self.pause[cur1]
                    
                    if np.random.random() > pause1:
                        self.occupied[cur1 - 1] = 1
                        self.occupied[cur1] = 0
                        
                        self.LEFs[i, 0] = cur1 - 1
                        
            if self.stalled[i, 1] == 0:
                if self.occupied[cur2 + 1] == 0:                    
                    pause2 = self.pause[cur2]
                    
                    if np.random.random() > pause2:
                        self.occupied[cur2 + 1] = 1
                        self.occupied[cur2] = 0
                        
                        self.LEFs[i, 1] = cur2 + 1
        
        
    def step(self):
        self.LEF_death()
        self.LEF_step()
        
    
    def steps(self, N):
        for _ in range(N):
            self.step()

        
class LEFTranslocatorDynamicBoundary(LEFTranslocator):
     
    def __init__(self,
                 numLEF,
                 deathProb,
                 stalledDeathProb,
                 birthArray,
                 pauseProb,
                 stallProbLeft,
                 stallProbRight,
                 ctcfDeathProb,
                 ctcfBirthProb,
                 *args):
            
        self.ctcfDeathProb = ctcfDeathProb
        self.ctcfBirthProb = ctcfBirthProb

        self.stallProbLeft_init = np.copy(stallProbLeft)
        self.stallProbRight_init = np.copy(stallProbRight)

        super().__init__(numLEF,
                         deathProb,
                         stalledDeathProb,
                         birthArray,
                         pauseProb,
                         stallProbLeft,
                         stallProbRight)


    def ctcf_death(self):
    
        for i in range(self.numSite):
            if self.stallProbLeft[i] != 0:
                if np.random.random() < self.ctcfDeathProb[i]:
                    self.stallProbLeft[i] = 0
                    
                    for j in range(self.numLEF):
                        if i == self.LEFs[j, 0]:
                            self.stalled[j, 0] = 0
                    
            if self.stallProbRight[i] != 0:
                if np.random.random() < self.ctcfDeathProb[i]:
                    self.stallProbRight[i] = 0
                    
                    for j in range(self.numLEF):
                        if i == self.LEFs[j, 1]:
                            self.stalled[j, 1] = 0
                          

    def ctcf_birth(self):
    
        for i in range(self.numSite):
            if self.stallProbLeft[i] != self.stallProbLeft_init[i]:
                if np.random.random() < self.ctcfBirthProb[i]:
                    self.stallProbLeft[i] = self.stallProbLeft_init[i]
                    
            if self.stallProbRight[i] != self.stallProbRight_init[i]:
                if np.random.random() < self.ctcfBirthProb[i]:
                    self.stallProbRight[i] = self.stallProbRight_init[i]
                        
                                
    def step(self):
        self.ctcf_death()
        self.ctcf_birth()
        
        super().step()
