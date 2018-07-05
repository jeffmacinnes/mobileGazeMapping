# Steps for submitting to JOSS

[https://joss.theoj.org/about](https://joss.theoj.org/about)

* Software available in open repo (e.g. GitHub)
* Author short markdown paper:
	* title
	* summary - describe high-level functionality, and purpose of the software.
	* author names/affiliations
	* key references, including a link to the software archive
	* ~250-1000 words total
* Metadata file to include in repo


# Reviewer Guidelines

* Is there a OSI approved license?
* Documentation should be sufficieint to understand core functionality of the software under review. High-level overview of this documentation should be included in a README file. There should be:
	* Statement of need: what problem does the software solve? who is the target audience?
	* Installation instructions: clearly-stated list of dependencies. Ideally in a requirements.txt file
	* Example Usage: examples of how to use the software in real-world analysis problems
	* Are all functions documented properly?
	* Tests: automated test suite hooked up to external service like Travis-CI or similar. OR documented manual steps that can be followed to check the expected functionality of the software (e.g. sample input file to assert behavior)
	* Clear guidelines for 3rd parties wishing to: Contribute, Report Issues or problems, or Seek Support


# To Do
- Make new repository for project
- Update all code documentation using Numpy Documentation standards and flake8 to confirm PEP8 standards. 
- Figure out proper dependencies, and make a requirements.txt file
- Include test data from each manufacturer. Look up how to use this test data in a Travis-CI manner
- Make sure there's a license file
- Make a thorough README file that includes: overview, installation instructions, example usage, and clear guidelines for 3rd party contributions, issue reporting, or support. 


# DemoData

- grabbing 