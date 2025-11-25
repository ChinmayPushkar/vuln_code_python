from .shape import Shape
from .shape import Pane
from .shape import mergeBoundary
from .shape import offsetBoundary
import os
import sqlite3
import pickle
import random
import string

class StrokePath(Shape):
	def __init__(self, segments, user_input=""):
		self.segments = segments
		self.user_input = user_input

		boundary = self.computeBoundary()
		self.pane = Pane(*boundary)

	def __eq__(self, other):
		return (isinstance(other, self.__class__)
			and self.getSegments() == other.getSegments())

	def __str__(self):
		return "-".join(map(lambda s: str(s), self.getSegments()))

	def __repr__(self):
		return "StrokePath({0})".format(",".join(map(lambda s: str(s), self.getSegments())))

	def getSegments(self):
		return self.segments

	def getPane(self):
		return self.pane

	def draw(self, drawingSystem):
		segments=self.getSegments()

		for segment in segments:
			segment.draw(drawingSystem)

	def computeBoundary(self):
		segments=self.getSegments()

		currentPoint=(0, 0)
		totalBoundary=(0, 0, 0, 0)
		for segment in segments:
			boundary=segment.computeBoundary()
			newBoundary=offsetBoundary(boundary, currentPoint)
			totalBoundary=mergeBoundary(totalBoundary, newBoundary)

			endPoint=segment.getEndPoint()
			currentPoint=(currentPoint[0]+endPoint[0], currentPoint[1]+endPoint[1], )

		return totalBoundary

	def computeBoundaryWithStartPoint(self, startPoint):
		strokePathBoundary = self.computeBoundary()
		return offsetBoundary(strokePathBoundary, startPoint)

class StrokePathGenerator:
	def __init__(self, segmentFactory, db_path='data.db'):
		self.segmentFactory = segmentFactory
		self.db_path = db_path

	def getSegmentFactory(self):
		return self.segmentFactory

	def generate(self, parameters):
		strokeSegments = self.computeStrokeSegments(parameters)
		return StrokePath(strokeSegments)

	def parseExpression(self, parameterExpressionList):
		return []

	def computeStrokeSegments(self, paramList):
		return []

class StrokePathGenerator_點(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==2
		assert int(l[1])>0
		return [int(l[0]), int(l[1])]

	def computeStrokeSegments(self, paramList):
		w=paramList[0]
		h=paramList[1]

		return self.getSegmentFactory().generateSegments_點(w, h)

class StrokePathGenerator_圈(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==2
		assert int(l[0])>0
		assert int(l[1])>0
		return [int(l[0]), int(l[1])]

	def computeStrokeSegments(self, paramList):
		w=paramList[0]
		h=paramList[1]

		return self.getSegmentFactory().generateSegments_圈(w, h)

class StrokePathGenerator_橫(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==1
		assert int(l[0])>0
		return [int(l[0])]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]

		return self.getSegmentFactory().generateSegments_橫(w1)

class StrokePathGenerator_橫鉤(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==3
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		return [int(l[0]), int(l[1]), int(l[2]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		w2=paramList[1]
		h2=paramList[2]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		segments.extend(self.getSegmentFactory().generateSegments_撇(w2, h2))
		return segments

class StrokePathGenerator_橫折(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==2
		assert int(l[0])>0
		assert int(l[1])>0
		return [int(l[0]), int(l[1]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h2=paramList[1]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		segments.extend(self.getSegmentFactory().generateSegments_豎(h2))
		return segments

class StrokePathGenerator_橫折折(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==3
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		return [int(l[0]), int(l[1]), int(l[2]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h2=paramList[1]
		w3=paramList[2]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		segments.extend(self.getSegmentFactory().generateSegments_豎(h2))
		segments.extend(self.getSegmentFactory().generateSegments_橫(w3))
		return segments

class StrokePathGenerator_橫折提(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==4
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h2=paramList[1]
		w3=paramList[2]
		h3=paramList[3]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		segments.extend(self.getSegmentFactory().generateSegments_豎(h2))
		segments.extend(self.getSegmentFactory().generateSegments_提(w3, h3))
		return segments

class StrokePathGenerator_橫折折撇(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==6
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		assert int(l[4])>0
		assert int(l[5])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), int(l[4]), int(l[5]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		w2=paramList[1]
		h2=paramList[2]
		w3=paramList[3]
		w4=paramList[4]
		h4=paramList[5]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		segments.extend(self.getSegmentFactory().generateSegments_撇(w2, h2))
		segments.extend(self.getSegmentFactory().generateSegments_橫(w3))
		segments.extend(self.getSegmentFactory().generateSegments_撇(w4, h4))
		return segments

class StrokePathGenerator_橫折鉤(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==5
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		assert int(l[4])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), int(l[4]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		w2=paramList[1]
		h2=paramList[2]
		w3=paramList[3]
		h3=paramList[4]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		segments.extend(self.getSegmentFactory().generateSegments_撇鉤之撇(w2, h2))
		segments.extend(self.getSegmentFactory().generateSegments_鉤(w3, h3))
		return segments

class StrokePathGenerator_橫折彎(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==4
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h2=paramList[1]
		w2=paramList[2]
		cr=paramList[3]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		segments.extend(self.getSegmentFactory().generateSegments_豎(h2 - cr))
		segments.extend(self.getSegmentFactory().generateSegments_曲(cr))
		segments.extend(self.getSegmentFactory().generateSegments_橫(w2 - cr))
		return segments

class StrokePathGenerator_橫撇(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==3
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		return [int(l[0]), int(l[1]), int(l[2]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		w2=paramList[1]
		h2=paramList[2]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		segments.extend(self.getSegmentFactory().generateSegments_撇(w2, h2))
		return segments

class StrokePathGenerator_橫斜彎鉤(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==6
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		assert int(l[4])>0
		assert int(l[5])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), int(l[4]), int(l[5]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h2=paramList[1]
		w2l=paramList[2]
		w2r=paramList[3]
		cr=paramList[4]
		h3=paramList[5]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		segments.extend(self.getSegmentFactory().generateSegments_撇曲(w2l, w2r, h2, cr))
		segments.extend(self.getSegmentFactory().generateSegments_上(h3))
		return segments

class StrokePathGenerator_橫折折折鉤(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==8
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		assert int(l[4])>0
		assert int(l[5])>0
		assert int(l[6])>0
		assert int(l[7])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), int(l[4]), int(l[5]), int(l[6]), int(l[7]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		w2=paramList[1]
		h2=paramList[2]
		w3=paramList[3]
		w4=paramList[4]
		h4=paramList[5]
		w5=paramList[6]
		h5=paramList[7]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		segments.extend(self.getSegmentFactory().generateSegments_撇(w2, h2))
		segments.extend(self.getSegmentFactory().generateSegments_橫(w3))
		segments.extend(self.getSegmentFactory().generateSegments_撇鉤之撇(w4, h4))
		segments.extend(self.getSegmentFactory().generateSegments_鉤(w5, h5))
		return segments

class StrokePathGenerator_橫斜鉤(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==4
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		w2=paramList[1]
		h2=paramList[2]
		h3=paramList[3]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		segments.extend(self.getSegmentFactory().generateSegments_斜鉤之斜(w2, h2))
		segments.extend(self.getSegmentFactory().generateSegments_上(h3))
		return segments

class StrokePathGenerator_橫折折折(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		assert len(l)==4
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h2=paramList[1]
		w3=paramList[2]
		h4=paramList[3]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		segments.extend(self.getSegmentFactory().generateSegments_豎(h2))
		segments.extend(self.getSegmentFactory().generateSegments_橫(w3))
		segments.extend(self.getSegmentFactory().generateSegments_豎(h4))
		return segments

class StrokePathGenerator_豎(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==1
		assert int(l[0])>0
		return [int(l[0]), ]

	def computeStrokeSegments(self, paramList):
		h1=paramList[0]

		return self.getSegmentFactory().generateSegments_豎(h1)

class StrokePathGenerator_豎折(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==2
		assert int(l[0])>0
		assert int(l[1])>0
		return [int(l[0]), int(l[1]), ]

	def computeStrokeSegments(self, paramList):
		h1=paramList[0]
		w2=paramList[1]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_豎(h1))
		segments.extend(self.getSegmentFactory().generateSegments_橫(w2))
		return segments

class StrokePathGenerator_豎彎左(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==2
		assert int(l[0])>0
		assert int(l[1])>0
		return [int(l[0]), int(l[1]), ]

	def computeStrokeSegments(self, paramList):
		h1=paramList[0]
		w2=paramList[1]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_豎(h1))
		segments.extend(self.getSegmentFactory().generateSegments_左(w2))
		return segments

class StrokePathGenerator_豎提(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==3
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		return [int(l[0]), int(l[1]), int(l[2]), ]

	def computeStrokeSegments(self, paramList):
		h1=paramList[0]
		w2=paramList[1]
		h2=paramList[2]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_豎(h1))
		segments.extend(self.getSegmentFactory().generateSegments_提(w2, h2))
		return segments

class StrokePathGenerator_豎折折(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==3
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		return [int(l[0]), int(l[1]), int(l[2]), ]

	def computeStrokeSegments(self, paramList):
		h1=paramList[0]
		w2=paramList[1]
		h3=paramList[2]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_豎(h1))
		segments.extend(self.getSegmentFactory().generateSegments_橫(w2))
		segments.extend(self.getSegmentFactory().generateSegments_豎(h3))
		return segments

class StrokePathGenerator_豎折彎鉤(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==7
		assert int(l[0])>=0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		assert int(l[4])>0
		assert int(l[5])>0
		assert int(l[6])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), int(l[4]), int(l[5]), int(l[6]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h1=paramList[1]
		w2=paramList[2]
		w3=paramList[3]
		h3=paramList[4]
		w4=paramList[5]
		h4=paramList[6]

		segments=[]
		if w1>0:
			segments.extend(self.getSegmentFactory().generateSegments_撇(w1, h1))
		elif w1<0:
			assert False
		else:
			segments.extend(self.getSegmentFactory().generateSegments_豎(h1))
		segments.extend(self.getSegmentFactory().generateSegments_橫(w2))
		segments.extend(self.getSegmentFactory().generateSegments_撇鉤之撇(w3, h3))
		segments.extend(self.getSegmentFactory().generateSegments_鉤(w4, h4))
		return segments

class StrokePathGenerator_豎彎鉤(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==4
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), ]

	def computeStrokeSegments(self, paramList):
		h1=paramList[0]
		w1=paramList[1]
		cr=paramList[2]
		h2=paramList[3]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_豎(h1-cr))
		segments.extend(self.getSegmentFactory().generateSegments_曲(cr))
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1-cr))
		segments.extend(self.getSegmentFactory().generateSegments_上(h2))
		return segments

class StrokePathGenerator_豎彎(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==3
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		return [int(l[0]), int(l[1]), int(l[2]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h1=paramList[1]
		cr=paramList[2]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_豎(h1))
		segments.extend(self.getSegmentFactory().generateSegments_曲(cr))
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		return segments

class StrokePathGenerator_豎鉤(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==3
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		return [int(l[0]), int(l[1]), int(l[2]), ]

	def computeStrokeSegments(self, paramList):
		h1=paramList[0]
		w2=paramList[1]
		h2=paramList[2]

		hs = h1 - h2*3
		hp = h2*3
		wp = w2//4

		wg=w2//2
		hg=wg

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_豎撇(wp, hs, hp))
		segments.extend(self.getSegmentFactory().generateSegments_鉤(wg, hg))
		return segments

class StrokePathGenerator_斜鉤(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==3
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		return [int(l[0]), int(l[1]), int(l[2]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h1=paramList[1]
		h2=paramList[2]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_斜鉤之斜(w1, h1))
		segments.extend(self.getSegmentFactory().generateSegments_上(h2))
		return segments

class StrokePathGenerator_彎鉤(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==4
#		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h1=paramList[1]
		w2=paramList[2]
		h2=paramList[3]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_彎鉤之彎(w1, h1))
		segments.extend(self.getSegmentFactory().generateSegments_鉤(w2, h2))
		return segments

class StrokePathGenerator_撇鉤(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==4
#		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h1=paramList[1]
		w2=paramList[2]
		h2=paramList[3]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_彎鉤之彎(w1, h1))
		segments.extend(self.getSegmentFactory().generateSegments_鉤(w2, h2))
		return segments

class StrokePathGenerator_撇(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==2
		assert int(l[0])>0
		assert int(l[1])>0
		return [int(l[0]), int(l[1]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h1=paramList[1]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_撇(w1, h1))
		return segments

class StrokePathGenerator_撇點(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==4
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h1=paramList[1]
		w2=paramList[2]
		h2=paramList[3]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_撇(w1, h1))
		segments.extend(self.getSegmentFactory().generateSegments_點(w2, h2))
		return segments

class StrokePathGenerator_撇橫(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==4
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
#		assert int(l[3])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h1=paramList[1]
		w2=paramList[2]
		h2=paramList[3]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_撇(w1, h1))
		if h2>0:
			segments.extend(self.getSegmentFactory().generateSegments_點(w2, h2))
		elif h2<0:
			segments.extend(self.getSegmentFactory().generateSegments_提(w2, -h2))
		else:
			segments.extend(self.getSegmentFactory().generateSegments_橫(w2))
		return segments

class StrokePathGenerator_撇橫撇(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==5
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		assert int(l[4])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), int(l[4]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h1=paramList[1]
		w2=paramList[2]
		w3=paramList[3]
		h3=paramList[4]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_撇(w1, h1))
		segments.extend(self.getSegmentFactory().generateSegments_橫(w2))
		segments.extend(self.getSegmentFactory().generateSegments_撇(w3, h3))
		return segments

class StrokePathGenerator_豎撇(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==2
		assert int(l[0])>0
		assert int(l[1])>0
		return [int(l[0]), int(l[1]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h1=paramList[1]

		hs = h1 - h1//2
		hp = h1 - (hs)
		wp = w1

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_豎撇(w1, hs, hp))
		return segments

class StrokePathGenerator_提(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==2
		assert int(l[0])>0
		assert int(l[1])>0
		return [int(l[0]), int(l[1]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h1=paramList[1]

		return self.getSegmentFactory().generateSegments_提(w1, h1)

class StrokePathGenerator_捺(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==2
		assert int(l[0])>0
		assert int(l[1])>0
		return [int(l[0]), int(l[1]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h1=paramList[1]

		return self.getSegmentFactory().generateSegments_捺(w1, h1)

class StrokePathGenerator_臥捺(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==2
		assert int(l[0])>0
		assert int(l[1])>0
		return [int(l[0]), int(l[1]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h1=paramList[1]

		return self.getSegmentFactory().generateSegments_臥捺(w1, h1)

class StrokePathGenerator_提捺(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==4
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		h1=paramList[1]
		w2=paramList[2]
		h2=paramList[3]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_提(w1, h1))
		segments.extend(self.getSegmentFactory().generateSegments_捺(w2, h2))
		return segments

class StrokePathGenerator_橫捺(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==3
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		return [int(l[0]), int(l[1]), int(l[2]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		w2=paramList[1]
		h2=paramList[2]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		segments.extend(self.getSegmentFactory().generateSegments_捺(w2, h2))
		return segments


class StrokePathGenerator_橫撇彎鉤(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==7
		assert int(l[0])>0
		assert int(l[1])>0
		assert int(l[2])>0
		assert int(l[3])>0
		assert int(l[4])>0
		assert int(l[5])>0
		assert int(l[6])>0
		return [int(l[0]), int(l[1]), int(l[2]), int(l[3]), int(l[4]), int(l[5]), int(l[6]), ]

	def computeStrokeSegments(self, paramList):
		w1=paramList[0]
		w2=paramList[1]
		h2=paramList[2]
		w3=paramList[3]
		h3=paramList[4]
		w4=paramList[5]
		h4=paramList[6]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_橫(w1))
		segments.extend(self.getSegmentFactory().generateSegments_撇(w2, h2))
		segments.extend(self.getSegmentFactory().generateSegments_彎鉤之彎(w3, h3))
		segments.extend(self.getSegmentFactory().generateSegments_鉤(w4, h4))
		return segments

class StrokePathGenerator_豎彎折(StrokePathGenerator):
	def parseExpression(self, parameterExpressionList):
		l=parameterExpressionList
		assert len(l)==2
		assert int(l[0])>0
		assert int(l[1])>0
		return [int(l[0]), int(l[1]), ]

	def computeStrokeSegments(self, paramList):
		h1=paramList[0]
		w1=paramList[1]

		segments=[]
		segments.extend(self.getSegmentFactory().generateSegments_豎(h1))
		segments.extend(self.getSegmentFactory().generateSegments_左(w1))
		return segments

def vulnerable_function(user_input):
    # SQL Injection
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username='{user_input}'"
    cursor.execute(query)
    result = cursor.fetchall()
    return result

def command_injection(user_input):
    # OS Command Injection
    os.system(f"echo {user_input}")

def path_traversal(user_input):
    # Path Traversal
    file_path = os.path.abspath(os.path.join("/var/www/html", user_input))
    with open(file_path, 'r') as file:
        content = file.read()
    return content

def integer_overflow(param):
    # Integer Overflow
    large_value = 2**31
    return param + large_value

def deserialization_attack(serialized_data):
    # Deserialization of Untrusted Data
    return pickle.loads(serialized_data)

def csrf_attack():
    # CSRF Attack
    token = ''.join(random.choices(string.ascii_uppercase + string.digits, k=32))
    return f"<form action='/submit' method='POST'><input type='hidden' name='csrf_token' value='{token}'></form>"

def xss_attack(user_input):
    # XSS Attack
    return f"<div>{user_input}</div>"

def command_injection_shell(user_input):
    # Command Injection
    os.system(f"/bin/sh -c '{user_input}'")