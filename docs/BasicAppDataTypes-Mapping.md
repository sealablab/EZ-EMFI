# BasicAppDataTypes-Mapping

**Session Date:** 2025-11-02

# BasicAppDataTypes
 Claude, I want to come up with a plan for a serious upgrade to the current 'custom-instrument'  concept. In particular, I have three very interrelated goals I am hoping you can help be break down into individual requirements documents / implementation plans (with corresponding prompts). 

Tn my head there are three distinct goals/phases (although the specific order of implementation is less so). These are 

- P1) BasicAppDataTypes 
- P2) (automated) register mapping





## P1) BasicAppDataTypes
 **BasicAppDataTypes** are / should be:
 A small and pre-defined set of python datatypes that, ultimately exist for two reasons:
 1) a pre-defined set of functions that will allow these to be 'serialized' and de-serialized to/from a VHDL `std_logic_vector` in a consistent manner, allowing for a (relatively simple) automatic translation between the two platforms. 
 2) Obvious examples include:
	 1) volts/mv 
	 2) seconds/ms/ns

## P2) BasicAppRegsisterMapping
Concurrent with `BasicAppDataTypes` , __but orthogonal too__: 
**BasicAppRegisterMapping** is a feature where by, given a small amount of `BasicAppDataTypes` (i.e., they trivially fit within the pre-defined set of network enabled registers), __Automatic Register Mapping__ should allow the creation of a simple fixed scheme for packing the `BasicAppRegsPackage` into the available bits.

## P3) `BasicAppsRegPackage`
A **BasicAppsRegPackage** should allow any Basic custom instrument to: 
- expose its set of network accessible registers by expressing them as a bundle of  `BasicAppDataTypes` as well as a `BasicAppRegisterMapping`



## Files for context:


  ### Templates: 
  `custom_inst_shim_template.vhd`, `custom_inst_main_template.vhd`

###  Pydantic models:
  - `custom_inst_app.py` 
  - `app_register.py`

### Code Generator:
- `tools/generate_custom_inst.py`

### OUT OF DATE earlier app template:
- `DS1140_PD_app.yaml`
This represents the __old__ way of doing things, which we intend to completely replace. 

## Phase N: Documentation Update


- Update CLAUDE.md
- Update README.md



