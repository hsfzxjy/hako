PY?=python3
N_TEST_TIMES?=5
HAKO_DEBUG?=1
TEST_FLAGS?=--showlocals
CAPTURE?=1
K?=
X?=

ifeq ($(CAPTURE), 1)
	CAPTURE_FLAG = ''
else
	CAPTURE_FLAG = -s
endif

ifeq ($(K),)
	KFLAG=
else
	KFLAG=-k $(K)
endif

ifeq ($(X),)
	XFLAG=
else
	XFLAG=-x
endif


test:
	N_TEST_TIMES=$(N_TEST_TIMES) HAKO_DEBUG=$(HAKO_DEBUG) $(PY) -m pytest tests/ -vv $(TEST_FLAGS) $(CAPTURE_FLAG) $(KFLAG) $(XFLAG)