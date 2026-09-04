# Evaluation Ground-Truth Set (80 items)

Manually labeled set for the DTSC 691 capstone evaluation: 20 job / 20 event / 20 mixed-ambiguous (lowest tagger-confidence items across categories) / 20 networking (random sample). Networking was appended after the original 60 as a lower-priority check on scrape quality.

**How to use:** for each item, fill in the `YOUR LABEL:` fields under "Human Tag" (tab/click into each blank and type your answer) *before* reading the `Auto-Tagged (system output)` block below it — it's placed after your answer on purpose so it can't bias your independent judgment. Check it only after you've committed to your own tag.

Note on scope: for Bucket 2 (Event) and Bucket 4 (Networking), only `category` is evaluable — `role_type`/`seniority`/`engagement_type`/`role_category`/`industry`/`company_stage` are structurally `None` for non-job items, so those Human Tag fields are omitted for those two buckets. This means the events/networking eval is a single classification-accuracy + confusion-matrix check, not a full F1 suite like Bucket 1 (Job) gets — that's an inherent data-shape limit, not an oversight.

---


## Bucket 1 — Job (20 items)

### Item 1 — DB id 5057

**Title:** Staff Software Engineer, Model Serving   
**Source:** greenhouse  
**Location:** San Francisco, California  
**URL:** https://databricks.com/company/careers/open-positions/job?gh_jid=8211647002

**Raw text (preview):**
```
At Databricks, we are passionate about enabling data teams to solve the world's toughest problems — from making the next mode of transportation a reality to accelerating the development of medical breakthroughs. We do this by building and running the world's best data and AI infrastructure platform so our customers can use deep data insights to improve their business. 


Databricks’ Model Serving product provides enterprises with a unified, scalable, and governed platform to deploy and manage AI/ML models — from traditional ML to fine-tuned and proprietary large language models. It offers real-time, low-latency inference, governance, monitoring, and lineage. As AI adoption accelerates, Model Serving is a core pillar of the Databricks platform, enabling customers to operationalize models at scale with strong SLAs and cost efficiency.


As a Staff Engineer, you’ll play a critical role in shaping both the product experience and the foundational infrastructure of Model Serving. You will design and build systems that enable high-throughput, low-latency inference across CPU and GPU workloads, influence architectural direction, and collaborate closely across platform, product, infrastructure, and research teams to deliver a world-class serving platform.


The impact you will have:




Design and implement core systems and APIs that power Databricks Model Serving, ensuring scalability, reliability, and operational excellence.


Partner with product and engineering leadership to defin

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `software engineer` | seniority: `staff+`
- engagement_type: `full_time` | role_category: `software_engineer` | industry: `ai_ml`
- remote_type: `hyperlocal_sf` | company_stage: `growth` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.96` | content_quality: `9.5`

---

### Item 2 — DB id 5852

**Title:** Lead, Process Excellence  
**Source:** greenhouse  
**Location:** Remote Netherlands  
**URL:** https://job-boards.greenhouse.io/affirm/jobs/7503006003

**Raw text (preview):**
```
Affirm is reinventing credit to make it more honest and friendly, giving consumers the flexibility to buy now and pay later without any hidden fees or compounding interest.
Affirm is seeking a senior leader to drive process excellence, training, knowledge management, and localization across our global Shared Services organization. In this role, you will define and execute the strategy that enables Affirm’s international operations to scale efficiently, compliantly, and with world-class customer and merchant experiences.


As an Operations Enablement Lead, you will set the vision for operational readiness, ensuring our people, processes, resources, and localized content evolve in lockstep with Affirm’s global growth. You will build and lead cross-functional initiatives to optimize workflows, strengthen knowledge systems, and design learning programs that accelerate performance across geographies and languages.You will partner closely with cross-functional stakeholders and augmented staff to drive operational readiness, streamline workflows, and deliver agent-facing resources that are accurate, engaging, and aligned with company goals and operational KPIs.


We are seeking a hands-on, data-driven leader who thrives in building efficient processes, structuring knowledge, and enabling high-impact learning for our global teams. This role will support both internal operations and external vendor/partner teams and will serve as a connector between global strategy and day-to-day exec

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `operations enablement lead` | seniority: `senior`
- engagement_type: `full_time` | role_category: `ops_admin` | industry: `fintech`
- remote_type: `remote` | company_stage: `public` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `9.0`

---

### Item 3 — DB id 7897

**Title:** Accommodation Administrator FIFO 14 7 Roster Cairns Queensland  
**Source:** remoteok  
**Location:** Queensland, Queensland, Australia  
**URL:** https://remoteOK.com/remote-jobs/remote-accommodation-administrator-fifo-14-7-roster-cairns-queensland-sodexo-1134252

**Raw text (preview):**
```
Tags: sys admin, marketing, c, admin, exec, engineer
<strong>Job Description<br><br></strong><strong>Help create a home away from home<br><br></strong><ul><li>14 days on, 7 days off roster</li><li>Immediate Start available</li><li>Opportunity to join the 18th largest employer globally and leader in quality of life services <br><br></li></ul><strong>About The Job<br><br></strong>Due to our continued growth Sodexo is seeking an experienced Accommodation Administrator to work across our Far North Queensland sites. Reporting to the Integrated Services Manger, your main responsibilities will entail high volume accommodation check-ins and flight bookings, data entry, database maintenance and receptionist duties.<br><br>This is a local hire role meaning you need to live in Weipa and surrounding suburbs however we will consider fly in fly out from Cairns for the right applicant.<br><br><strong>About You<br><br></strong>You will consider yourself a well organised, self-motivated individual and hospitality professional with the ability to the below criteria:<br><br><ul><li>Accommodation reservation experience (In-flight) preferable in a remote village, resort or similar environment</li><li>Administration experience supporting a very fast paced team</li><li>Inflight Accommodation system knowledge desirable but not essential</li><li>Intermediate to advanced proficiency in MS Office Suite </li><li>Excellent written and verbal communication skills are essential</li><li>Proven ability to li

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `accommodation administrator` | seniority: `junior`
- engagement_type: `full_time` | role_category: `ops_admin` | industry: `other`
- remote_type: `other` | company_stage: `public` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.75` | content_quality: `6.5`

---

### Item 4 — DB id 9333

**Title:**  Senior Revenue Accountant  
**Source:** ashby  
**Location:** Toronto  
**URL:** https://jobs.ashbyhq.com/cohere/1e2d0f32-774f-4061-954d-0e28bfe054ca

**Raw text (preview):**
```
Business Operations, FullTime
Who are we?
Cohere is the leading security-first enterprise AI company.  We build cutting-edge foundation AI models and end-to-end products that are designed to solve real-world business problems.
We’re training and deploying frontier models for enterprises who are building AI systems. We believe that our work is instrumental to the widespread adoption of AI and we are looking for folks that want to be part of that.
We obsess over what we build. Each one of us is responsible for contributing to increasing the capabilities of our models and the value they drive for our customers. Cohere is a team of researchers, engineers, designers, and more, who are all passionate about their craft.
We are a global technology company co-headquartered in Toronto and San Francisco, with key offices in London, New York City, Montreal, Seoul, Germany and Paris. Join us!
As a Senior Revenue Accountant at Cohere, you will: 
Perform detailed contract review and analysis for non-standard arrangements to determine appropriate revenue recognition treatment in accordance with ASC 606 
Lead and execute all revenue- and commission-related month-end, quarter-end, and year-end close activities 
Prepare and review monthly balance sheet reconciliations for all revenue, commission, and related accounts, including deferred revenue, accounts receivable, and contract assets 
Serve as a primary point of contact for external auditors on all revenue-related matters, providing comprehen

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `Senior Revenue Accountant` | seniority: `senior`
- engagement_type: `full_time` | role_category: `ops_admin` | industry: `ai_ml`
- remote_type: `other` | company_stage: `growth` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `9.0`

---

### Item 5 — DB id 14649

**Title:** Principal Data Scientist - Cloud Gaming and AI  
**Source:** linkedin_apify  
**Location:** Santa Clara, CA  
**URL:** https://www.linkedin.com/jobs/view/principal-data-scientist-cloud-gaming-and-ai-at-nvidia-ai-4429461154?position=2&pageNum=10&refId=JyS2jb053Akr2LI4DHV9oQ%3D%3D&trackingId=F0nwmBbHVMTAVyPLa%2BDOGw%3D%3D

**Raw text (preview):**
```
Not Applicable, Full-time
Job Requisition ID

JR2019886

Job Category

IT - Information Technology

Time Type

Full time

Join the NVIDIA GeForce NOW cloud team that allows users to play high-quality PC games on various devices, without the need for a dedicated gaming PC or console. NVIDIA's GeForce NOW service is built on top of our GPU technology, including our proprietary GPU architectures and software optimizations allowing efficient and high-quality experience even at high resolutions and fps and at industry leading low latencies.

Our team is building the Diagnostic, Prescriptive and AI-augmented Analytics solutions that encompass processing, visualization, anomaly detection, root cause and predictive modeling for the benefit of millions of our end users. Our active projects include real-time forecasting of demand, constraint-optimized capacity allocation, dynamic prescriptions per session, Customer Onboarding and Voice of Customer Analytics, targeted Customer Outreach campaigns based on Customer Retention modeling, effective personalized diagnostic recommendations, LLM Chatbot. You will wield the power of Data and AI to help globally deliver a best-in-class cloud computing/streaming performance and experience. Our technology stack relies on industry standard components and tools (Python, R, Pandas, JupyterLab, Spark, SQL, Databricks, MLFlow, Delta Lake, Grafana, Kibana, Kubeflow, Elyra, Kubernetes, Gitlab, CI/CD, MLOps, Kafka, SQS, Kubernetes)

What You'll Be Doing

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `data scientist` | seniority: `senior`
- engagement_type: `full_time` | role_category: `data_scientist` | industry: `hardware_semiconductor`
- remote_type: `bay_area` | company_stage: `public` | spam_risk: `clean`
- deadline: `2026-06-26` | tag_confidence: `0.95` | content_quality: `9.0`

---

### Item 6 — DB id 15759

**Title:** Senior Software Engineer  
**Source:** wellfound_search  
**Location:** San Francisco  
**URL:** https://wellfound.com/company/mithrl-1/jobs/senior-software-engineer

**Raw text (preview):**
```
$175k – $220k, full-time, via role search: ai-engineer
**ABOUT MITHRL**

*We imagine a world where new medicines reach patients in months, not years, and where scientific breakthroughs happen at the speed of thought.*

Mithrl is building the world’s first commercially available AI Co-Scientist. It is a discovery engine that transforms messy biological data into insights in minutes. Scientists ask questions in natural language, and Mithrl responds with real analysis, novel targets, hypotheses, and patent-ready reports.

**Our traction speaks for itself:**

- 12X year-over-year revenue growth
- Trusted by leading biotechs and big pharma across three continents
- Driving real breakthroughs from target discovery to patient outcomes.

**ABOUT THE ROLE**

We are hiring a **Senior Full Stack Engineer** to help build, scale, and evolve the core Mithrl product. This is a highly product-oriented engineering role with deep ownership across frontend, backend, and system design. You will work closely with product, design, ML, and scientific teams to turn complex scientific workflows into intuitive, high-performance software used daily by world-class researchers.

As a senior engineer, you will be responsible not just for execution, but for **technical direction, architectural decisions, and setting engineering standards**. You will own features end-to-end, from initial concept through production, iteration, and scale. This role requires strong full-stack engineering fundamentals, a bias t

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `senior full stack engineer` | seniority: `senior`
- engagement_type: `full_time` | role_category: `software_engineer` | industry: `biotech_health`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.85` | content_quality: `6.5`

---

### Item 7 — DB id 16271

**Title:** Senior Mechanical Engineer  
**Source:** wellfound_search  
**Location:** San Francisco  
**URL:** https://wellfound.com/company/pax-labs/jobs/senior-mechanical-engineer

**Raw text (preview):**
```
$180k – $235k, full-time, via role search: data-engineer
**THE COMPANY**

At PAX, we’re on a mission to enhance people’s lives through exceptional consumer experiences—honoring the plant through pioneering innovation, science-backed quality, and award-winning design. For nearly two decades, PAX has delivered high performance products crafted for precision, purity, and consistency that are trusted by millions worldwide.

Our culture is built on putting people at the center of everything we do, making an impact together, and having fun along the way. We believe exceptional products, a thriving employee experience, and strong operational rhythms go hand-in-hand. PAX has been recognized for its brand, culture and products by The New York Times’ Wirecutter, TIME, Fast Company, GQ, Gear Patrol, mg Magazine, High Times, and many more. PAX is certified Plastic Negative across all product lines by rePurpose Global, ensuring that twice as much plastic is removed from nature as is used in its products.

**ROLE AND RESPONSIBILITIES**

Reporting to the Director, Mechanical Engineering, the Senior Mechanical Engineer will be responsible for designing new products that are innovative, cost efficient, reliable, and ship on schedule. You will troubleshoot and make improvements to existing products, and work closely with other members of the engineering staff to create optimal solutions to difficult design, structural, thermal, and battery life issues. You will be comfortable sketching and pro

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `mechanical engineer` | seniority: `senior`
- engagement_type: `full_time` | role_category: `other` | industry: `consumer_gaming`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.9` | content_quality: `1.5`

---

### Item 8 — DB id 17015

**Title:** Principal Software Engineer ADEM (ADEM - Autonomous Digital Experience Management) - Windows  
**Source:** indeed_apify_old  
**Location:** Santa Clara, CA 95054  
**URL:** https://www.indeed.com/viewjob?jk=6fa16a98759cd4b1

**Raw text (preview):**
```
Full-time, $147,000 - $237,500 a year
Santa Clara, California, United States Product Engineering Ref ID: JR-019097

Our Mission

At Palo Alto Networks®, we’re united by a shared mission—to protect our digital way of life. We thrive at the intersection of innovation and impact, solving real-world problems with cutting-edge technology and bold thinking. Here, everyone has a voice, and every idea counts. If you’re ready to do the most meaningful work of your career alongside people who are just as passionate as you are, you’re in the right place.

Who We Are

In order to be the cybersecurity partner of choice, we must trailblaze the path and shape the future of our industry. This is something our employees work at each day and is defined by our values: Disruption, Collaboration, Execution, Integrity, and Inclusion. We weave AI into the fabric of everything we do and use it to augment the impact every individual can have. If you are passionate about solving real-world problems and ideating beside the best and the brightest, we invite you to join us!

We believe collaboration thrives in person. That’s why most of our teams work from the office full time, with flexibility when it’s needed. This model supports real-time problem-solving, stronger relationships, and the kind of precision that drives great outcomes.

Job Summary

Your Career

Palo Alto Networks' ADEM (Autonomous Digital Experience Management) group is seeking an accomplished Principal Engineer with expertise in develop

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `software engineer` | seniority: `staff+`
- engagement_type: `full_time` | role_category: `software_engineer` | industry: `enterprise_saas`
- remote_type: `bay_area` | company_stage: `public` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.95` | content_quality: `9.0`

---

### Item 9 — DB id 19449

**Title:** AI Platform Engineer, Backend  
**Source:** indeed_radius  
**Location:** San Francisco, CA  
**URL:** https://www.indeed.com/m/viewjob?jk=6dcd3c5b44130691&from=serp&tk=1jsje57rhi9er801&xkcb=SoAe67M3hTUa3hQpSJ0abzkdCdPP

**Raw text (preview):**
```
Full-time
About Brain Co.

Brain Co. is an applied AI startup co-founded by Jared Kushner and Elad Gil, and backed by leading Silicon Valley builders including Patrick Collison and Andrej Karpathy.

We are building AI applications for the world’s most important institutions, delivering impact on real-world problems across governments, healthcare systems, and critical industries.

Our progress so far:

Automated construction permitting for a sovereign government 80% faster, unlocking $375M+ in value

Optimized supply chains for a leading global energy company 30% lower cost, 99% reliability, preventing $100M+ in losses

Streamlined hospital patient care across national health systems 40% better outcomes, 80% less admin work

Company momentum:

Raised a $55M Series A from leading investors

Built a team of 70+ AI experts from Tesla, Google DeepMind, NVIDIA, and Databricks

At Brain Co., we focus on applying frontier AI to real institutional challenges, working alongside governments, healthcare systems, and critical industries to modernize how essential services operate.

We are looking for leaders who want to help bring new technology into institutions that impact millions of people.

About the role:

As a Backend Engineer at Brain Co., you'll own the systems that power our AI platform end-to-end, from architecture and design to deployment and maintenance. You'll build reliable, production-grade infrastructure for enterprise and government environments, solve complex problems f

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `backend engineer` | seniority: `mid`
- engagement_type: `full_time` | role_category: `software_engineer` | industry: `ai_ml`
- remote_type: `hyperlocal_sf` | company_stage: `series_a_b` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `9.0`

---

### Item 10 — DB id 20551

**Title:** Senior Accountant, Accounts Payable  
**Source:** greenhouse  
**Location:** Dallas, TX  
**URL:** https://coreweave.com/careers/job?4693203006&board=coreweave&gh_jid=4693203006

**Raw text (preview):**
```
CoreWeave is The Essential Cloud for AI™. Built for pioneers by pioneers, CoreWeave delivers a platform of technology, tools, and teams that enables innovators to build and scale AI with confidence. Trusted by leading AI labs, startups, and global enterprises, CoreWeave combines superior infrastructure performance with deep technical expertise to accelerate breakthroughs and turn compute into capability. Founded in 2017, CoreWeave became a publicly traded company (Nasdaq: CRWV) in March 2025. Learn more at 
www.coreweave.com
.








What You'll Do:


The 
Global Business Services (GBS)
 team at CoreWeave is responsible for centralizing, standardizing, and scaling foundational business processes across Finance, Procurement, and HR. As part of GBS, the Accounts Payable function plays a critical role in CoreWeave's Procure-to-Pay (P2P) process, ensuring operational excellence, strong controls, and high-quality service delivery as the company scales globally in a public-company environment.


As a Senior AP Accountant, Direct Spend, you are a critical member of CoreWeave's GBS organization, responsible for executing day-to-day accounts payable operations while supporting the end-to-end Procure-to-Pay (P2P) process. This role blends hands-on operational expertise with leadership in process standardization and continuous improvement initiatives. Partnering closely with GBS leadership, Accounting, Procurement, and external vendors, you will ensure accurate, timely, and scalable AP

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `accounts payable accountant` | seniority: `senior`
- engagement_type: `full_time` | role_category: `ops_admin` | industry: `ai_ml`
- remote_type: `other` | company_stage: `public` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `8.5`

---

### Item 11 — DB id 20813

**Title:** Senior Cloud Network Engineer   
**Source:** greenhouse  
**Location:** Bristol, UK  
**URL:** https://job-boards.greenhouse.io/graphcore/jobs/8561919002

**Raw text (preview):**
```
About Graphcore
 


How often do you get the chance to build a technology that transforms the future of humanity?
 


At Graphcore, we’re building the future of AI compute.We’re a team of semiconductor, software and AI experts, with deep experience in creating the complete AI compute stack - from silicon and software to infrastructure at datacenter scale. As part of the SoftBank Group, backed by significant long-term investment, we are delivering key technology into the fast-growing SoftBank AI ecosystem.To meet the vast and exciting AI opportunity, Graphcore is expanding its teams around the world.We are bringing together the brightest minds to solve the toughest problems, in a place where everyone has the opportunity to make an impact on the company, our products and the future of artificial intelligence.
 
 


Job Summary 
 
We are looking for a 
Senior 
Network 
Engineer 
to join our Cloud 
Platform
 Team
 and help develop and deploy clouds and services
. Working closely with our colleagues in 
Software 
Platform, Datacentre Operations and Product Development teams, you will 
deploy services on
our fleet of 
cutting-edge
 AI systems. As part of our 
Software 
Platform organisation, you will be involved in the cloud integration, validation, performance benchmarking, optimisation, and development of our high-performance AI solutions
.  
These include in-house AI systems alongside off-the-shelf high-performance servers, 
switches
 and storage solutions
.  
This is a hand-on

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `cloud network engineer` | seniority: `senior`
- engagement_type: `full_time` | role_category: `devops_infra_engineer` | industry: `hardware_semiconductor`
- remote_type: `other` | company_stage: `growth` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `9.0`

---

### Item 12 — DB id 20821

**Title:** Senior Engineering Program Coordinator   
**Source:** greenhouse  
**Location:** Austin, Texas, United States  
**URL:** https://job-boards.greenhouse.io/graphcore/jobs/8552045002

**Raw text (preview):**
```
About us


Graphcore is one of the world’s leading innovators in Artificial Intelligence compute.


It is developing hardware, software and systems infrastructure that will unlock the next generation of AI breakthroughs and power the widespread adoption of AI solutions across every industry.


As part of the SoftBank Group, Graphcore is a member of an elite family of companies responsible for some of the world’s most transformative technologies. Together, they share a bold vision: to enable Artificial Super Intelligence and ensure its benefits are accessible to everyone.


Graphcore’s teams are drawn from diverse backgrounds and bring a broad range of skills and perspectives. A melting pot of AI research specialists, silicon designers, software engineers and systems architects, Graphcore brings together people who are passionate about solving complex technical challenges.


Job Summary


Reporting to an Engineering Program Manager or Engineering Operations leader, the Senior Engineering Program Coordinator supports the planning, coordination and execution of engineering programs across multiple teams. The role is responsible for maintaining program schedules, tracking actions and dependencies, facilitating communication between stakeholders, and helping ensure engineering activities are delivered efficiently and on time. The successful candidate will play a key role in enabling collaboration, improving operational effectiveness and supporting the successful delivery of engine

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `Engineering Program Coordinator` | seniority: `senior`
- engagement_type: `full_time` | role_category: `ops_admin` | industry: `hardware_semiconductor`
- remote_type: `other` | company_stage: `growth` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `8.5`

---

### Item 13 — DB id 24748

**Title:** Clinical Nurse (RN), Cardiovascular Transplant Surgery - 1.0 FTE, Days (10HR)  
**Source:** indeed_radius  
**Location:** Palo Alto, CA 94305  
**URL:** https://www.indeed.com/viewjob?jk=7e546d432d88f7ba

**Raw text (preview):**
```
Full-time, $96.35 - $111.14 an hour
1.0 FTE Full time Day - 10 Hour R2657170 Onsite 107078002 CV Transplant Sugery Multi Site Nursing PALO ALTO, 300 Pasteur Dr, California

If you're ready to be part of our legacy of hope and innovation, we encourage you to take the first step and explore our current job openings. Your best is waiting to be discovered.

Day - 10 Hour (United States of America)

Preferred Qualifications:
• Strong background in cardiac care/cardiology
• Minimum of 2 years of experience in the Operating Room, Critical Care Units, Cath Lab, or other relevant clinical settings

This is a Stanford Health Care job.

A Brief Overview
The Clinical Nurse (CN) is an RN who provides hands-on care to patients, practicing in an evidence-based manner, within the Scope of Practice of the California Nursing Practice Act, regulatory requirements, standards of care, and hospital policies. Within that role, the CN performs all steps of the nursing process, including assessing patients; interpreting data; planning, implementing, and evaluating care; coordinating care with other providers; and teaching the patient and family the knowledge and skills needed to manage their care and prevent complications. The CN partners with the patient's family wherever possible, considering all aspects of care, to deliver family centered care. As a professional, monitors the quality of nursing care provided.

The Clinical Nurse is responsible for his/her own professional development, including li

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `clinical nurse (RN)` | seniority: `mid`
- engagement_type: `full_time` | role_category: `other` | industry: `health_general`
- remote_type: `bay_area` | company_stage: `public` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `8.5`

---

### Item 14 — DB id 27459

**Title:** Senior Robotics Software Engineer, Maritime  
**Source:** greenhouse  
**Location:** Costa Mesa, California, United States  
**URL:** https://boards.greenhouse.io/andurilindustries/jobs/5051589007?gh_jid=5051589007

**Raw text (preview):**
```
Anduril Industries is a defense technology company with a mission to transform U.S. and allied military capabilities with advanced technology. By bringing the expertise, technology, and business model of the 21st century’s most innovative companies to the defense industry, Anduril is changing how military systems are designed, built and sold. Anduril’s family of systems is powered by Lattice OS, an AI-powered operating system that turns thousands of data streams into a realtime, 3D command and control center. As the world enters an era of strategic competition, Anduril is committed to bringing cutting-edge autonomy, AI, computer vision, sensor fusion, and networking technology to the military in months, not years.
ABOUT THE TEAM


Anduril’s Maritime Division has assembled a diverse team of experts in software, robotics, artificial intelligence, sensor fusion, and data analysis to create software and hardware solutions that radically evolve the capabilities of our customers. We are fielding the next generation of autonomous systems to tackle the extremely challenging industry demands of maritime operations. Anduril has brought to market a unique, ultra-long-range, full-ocean-depth underwater vessel platform and a completely refreshed maritime vehicle and flexible manufacturing architecture that scales from "small" to "extra-large" vehicle sizes. Today, Anduril is executing on billion-dollar contracts while simultaneously performing Robot-as-a-Service (RaaS) AUV operations.
We

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `robotics software engineer` | seniority: `senior`
- engagement_type: `full_time` | role_category: `software_engineer` | industry: `government_defense`
- remote_type: `other` | company_stage: `growth` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `9.0`

---

### Item 15 — DB id 28152

**Title:** Tracking Software Engineer, Space  
**Source:** greenhouse  
**Location:** Washington, District of Columbia, United States  
**URL:** https://boards.greenhouse.io/andurilindustries/jobs/5114861007?gh_jid=5114861007

**Raw text (preview):**
```
Anduril Industries is a defense technology company with a mission to transform U.S. and allied military capabilities with advanced technology. By bringing the expertise, technology, and business model of the 21st century’s most innovative companies to the defense industry, Anduril is changing how military systems are designed, built and sold. Anduril’s family of systems is powered by Lattice OS, an AI-powered operating system that turns thousands of data streams into a realtime, 3D command and control center. As the world enters an era of strategic competition, Anduril is committed to bringing cutting-edge autonomy, AI, computer vision, sensor fusion, and networking technology to the military in months, not years.
ABOUT THE TEAM


Anduril's Space team is dedicated to expanding our AI-powered capabilities into the final frontier, enhancing Space Domain Awareness, Space Control, and Command and Control for U.S. military and allied partners. We're developing fully integrated hardware and software systems, including Lattice for Space Missions and modular payloads, to address growing threats in space and ensure our Guardians maintain a decisive advantage in this contested war-fighting domain.


ABOUT THE JOB


We are looking for a Tracking Software Engineer to join our rapidly growing team in Washington DC. In this role, you will be responsible for developing 2D and 3D tracking algorithms that maintain custody of space objects, processing sensor detections and messages into action

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `tracking software engineer` | seniority: `mid`
- engagement_type: `full_time` | role_category: `software_engineer` | industry: `government_defense`
- remote_type: `other` | company_stage: `growth` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `9.5`

---

### Item 16 — DB id 28456

**Title:** Electromechanical Technician (Starshield)  
**Source:** greenhouse  
**Location:** Hawthorne, CA  
**URL:** https://boards.greenhouse.io/spacex/jobs/8569955002?gh_jid=8569955002

**Raw text (preview):**
```
SpaceX was founded under the belief that a future where humanity is out exploring the stars is fundamentally more exciting than one where we are not. Today SpaceX is actively developing the technologies to make this possible, with the ultimate goal of enabling human life on Mars.
ELECTROMECHANICAL TECHNICIAN (STARSHIELD)
Starshield leverages SpaceX's Starlink technology and launch capability to support national security efforts. While Starlink is designed for consumer and commercial use, Starshield is designed for government use, with an initial focus on three areas: Earth observation, communications, and hosted payloads. Designed to meet diverse mission requirements, Starshield satellites are capable of integrating a wide variety of payloads, offering unique versatility to users. With the proven ability to iterate rapidly, SpaceX's unique full-stack approach in developing end-to-end systems, from launch vehicles to user terminals, enables the deployment of capabilities at scale with unprecedented speed. Starshield's proliferated low-Earth orbit architecture provides inherent resiliency and constant connectivity to on-orbit assets, while SpaceX's proven rapid launch capability provides expedient and economical access to space.


RESPONSIBILITIES: 




Fabricate and assemble high-quality, high-reliability electromechanical assemblies


Self-monitor work progress against area benchmarks and achieve on-time delivery of all work


Read, interpret, and work from drawings as well a

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `electromechanical technician` | seniority: `junior`
- engagement_type: `full_time` | role_category: `ops_admin` | industry: `hardware_semiconductor`
- remote_type: `other` | company_stage: `public` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `8.5`

---

### Item 17 — DB id 30059

**Title:** Planning Manager - GOC  
**Source:** greenhouse  
**Location:** Remote, USA  
**URL:** https://careers.withwaymo.com/jobs?gh_jid=7858106

**Raw text (preview):**
```
Waymo is an autonomous driving technology company with the mission to be the world's most trusted driver. Since its start as the Google Self-Driving Car Project in 2009, Waymo has focused on building the Waymo Driver—The World's Most Experienced Driver™—to improve access to mobility while saving thousands of lives now lost to traffic crashes. The Waymo Driver powers Waymo’s fully autonomous ride-hail service and can also be applied to a range of vehicle platforms and product use cases. The Waymo Driver has provided over ten million rider-only trips, enabled by its experience autonomously driving over 100 million miles on public roads and tens of billions in simulation across 15+ U.S. states.
Waymo Operations exists to deliver the Waymo Driver to the world. We are a global team building and scaling the world's first and leading autonomous fleet and operations platform. From component sourcing to end customer management, we enable and create value for Waymo through scaled and orchestrated deployment of the Waymo Driver. At Waymo, we are dedicated to building a culture that promotes collaboration and celebration. We value our team members' unique backgrounds, perspectives, and experiences and support and encourage all team members to share their ideas to help Waymo better serve the communities in which we operate.


This role follows a hybrid work schedule and reports to the Head of Global Operations Planning.


 


 


You will:






Design Scalable Processes:
 Build and own t

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `operations manager` | seniority: `mid`
- engagement_type: `full_time` | role_category: `ops_admin` | industry: `robotics`
- remote_type: `remote` | company_stage: `growth` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `9.0`

---

### Item 18 — DB id 31607

**Title:** Senior Counsel (Regulatory)  
**Source:** greenhouse  
**Location:** BLANK,BLANK,Multiple Locations  
**URL:** https://epicgames.com/careers/jobs/5995038004?gh_jid=5995038004

**Raw text (preview):**
```
WHAT MAKES US EPIC?


At the core of Epic’s success are talented, passionate people. Epic prides itself on creating a collaborative, welcoming, and creative environment. Whether it’s building award-winning games or crafting engine technology that enables others to make visually stunning interactive experiences, we’re always innovating.


Being Epic means being a part of a team that continually strives to do right by our community and users. We’re constantly innovating to raise the bar of engine and game development.
LEGAL


What We Do


Epic's multi-specialized team of attorneys and legal professionals partner across our organization to provide legal solutions as well as consult and inform on the products we build and games we develop.


What You'll Do


Epic’s regulatory team advises the company on newly enacted laws and regulations around the world as well as works alongside our Public Policy Team to monitor regulatory developments. Partnering closely with our subject matter experts, Product Counsel and Compliance Team, you will manage the design of compliance programs and educate counsel regarding regulatory requirements. You will also assist with the company’s response to regulatory investigations and requests for information from regulators.


In this role, you will




Advise Epic senior management, Product Counsel, the Compliance Team and Legal leadership on key global laws and regulations, including online safety frameworks


Lead multi-stakeholder regulatory complian

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `regulatory counsel` | seniority: `senior`
- engagement_type: `full_time` | role_category: `ops_admin` | industry: `consumer_gaming`
- remote_type: `other` | company_stage: `public` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `9.0`

---

### Item 19 — DB id 33977

**Title:** Director of Office of the CEO, Founder in Residence   
**Source:** greenhouse  
**Location:** Menlo Park, CA  
**URL:** https://job-boards.greenhouse.io/billiontoone/jobs/4707633005

**Raw text (preview):**
```
A Rare Opportunity to Shape the Future of Genomics


Join a team of brilliant, passionate innovators determined to transform healthcare. At BillionToOne, we've built a category-defining, publicly traded company on Nasdaq where transparency fuels trust, collaboration drives breakthroughs, and every contribution moves the needle on our mission to make life-changing diagnostics accessible to all. We don't just aim for incremental improvements; we build products that are 10x better than anything that exists today.


Our scientists, engineers, sales executives, and visionaries are united by an unwavering commitment to changing the standard of care in prenatal and cancer diagnostics. This is where cutting-edge science meets human compassion, and every innovation you contribute helps remove the fear of the unknown from some of life's most critical medical moments.


If you're driven by purpose, energized by innovation, and ready to help shape the future of precision medicine at scale, this is where you belong.
We are seeking exceptional entrepreneurial builders to join BillionToOne's newly launched 
Founder in Residence Program
 as a 
Director, Office of the CEO
. In this 12 to 18 month program, you will work directly with the CEO and Chief of Staff on the company's highest-priority strategic and operational projects, and graduate into a permanent senior operating role at the Director or Senior Director level.


This is one of the highest-leverage roles at BillionToOne. You will be

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `Director of Office of the CEO` | seniority: `senior`
- engagement_type: `full_time` | role_category: `ops_admin` | industry: `biotech`
- remote_type: `bay_area` | company_stage: `public` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `9.5`

---

### Item 20 — DB id 34567

**Title:** Lead Autonomy Behavior Engineer  
**Source:** greenhouse  
**Location:** Anywhere, USA  
**URL:** https://job-boards.greenhouse.io/maymobility/jobs/8551864002

**Raw text (preview):**
```
May Mobility is transforming cities through autonomous technology to create a safer, greener, more accessible world. Based in Ann Arbor, Michigan, May develops and deploys autonomous vehicles (AVs) powered by our innovative Multi-Policy Decision Making (MPDM) technology that literally reimagines the way AVs think.
Our vehicles do more than just drive themselves - they provide value to communities, bridge public transit gaps and move people where they need to go safely, easily and with a lot more fun. We’re building the world’s best autonomy system to reimagine transit by minimizing congestion, expanding access and encouraging better land use in order to foster more green, vibrant and livable spaces. Since our founding in 2017, we’ve given more than 500,000 autonomous rides to real people around the globe. And we’re just getting started. We’re hiring people who share our passion for building the future, today, solving real-world problems and seeing the impact of their work. Join us.
Essential Responsibilities




Design, implement, and test-state-of-the-art robotics software in C/C++ to enable comfortable and safe behavior and control for Autonomous Vehicles


Lead and participate in team code quality activities including design and code reviews 


Provide technical guidance to Technical Support Team on issue diagnosis and resolution


Coordinate with cross functional teams to develop software and system requirements for Autonomous Vehicle behavior and controls subsystems


Co

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `autonomy behavior engineer` | seniority: `senior`
- engagement_type: `full_time` | role_category: `software_engineer` | industry: `robotics`
- remote_type: `other` | company_stage: `growth` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `9.0`

---


## Bucket 2 — Event (20 items)

### Item 21 — DB id 504

**Title:** Body is the Interface workshop (Zach Lieberman <> tiat)  
**Source:** luma_events  
**Location:** tiat, 151 Powell St, San Francisco, CA 94102, USA  
**URL:** https://lu.ma/zachlieberman

**Raw text (preview):**
```
This hands-on workshop explores how the body can become an expressive tool for creative computation. Using p5.js and machine learning techniques like pose estimation, participants will learn how to connect movement and gesture to dynamic visual outputs. We’ll focus especially on the intersection of typography and the body, creating systems where physical motion shapes, distorts, or animates text. Participants will also explore interaction techniques like gesture recognition and body-based input to design playful, poetic, and embodied interfaces. No prior experience with machine learning is necessary, just curiosity and a willingness to move.
Zach Lieberman
 is an artist, researcher, and educator with a simple goal: he wants you surprised. In his work, he creates performances and installations that take human gesture as input and amplify them in different ways — making drawings come to life, imagining what the voice might look like, and transforming people’s silhouettes into music.  He’s been listed as one of Fast Company’s Most Creative People, he’s won the Golden Nica from Ars Electronica, Interactive Design of the Year from Design Museum London as well as listed in Time Magazine’s Inventions of the Year. He creates artwork through writing software and is a co-creator of 
openFrameworks
, an open source C++ toolkit for creative coding and helped co-found the 
School for Poetic Computation
, a school examining the lyrical possibilities of code. He is a professor at MIT Media

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.85` | content_quality: `6.5`

---

### Item 22 — DB id 520

**Title:** World's largest design picnic | Config 2026 Wind-down Picnic with Design Buddies & friends! 🐰  
**Source:** luma_events  
**Location:** Alamo Square Park, Hayes St, San Francisco, CA 94117, USA  
**URL:** https://lu.ma/azhjlwuv

**Raw text (preview):**
```
World's largest design picnic | Config 2026 Wind-down Picnic with Design Buddies & friends! 🐰
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.85` | content_quality: `1.0`

---

### Item 23 — DB id 535

**Title:** THE AI Engineer Afterparty  
**Source:** luma_events  
**Location:** San Francisco, CA  
**URL:** https://lu.ma/composio-lh5g

**Raw text (preview):**
```
THE AI Engineer Afterparty
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.5` | content_quality: `5.5`

---

### Item 24 — DB id 7351

**Title:** AWS Agentic AI Summit with MongoDB Mastra  
**Source:** meetup  
**Location:** San Francisco, CA  
**URL:** https://www.meetup.com/sfbay-ai/events/315494713/

**Raw text (preview):**
```
Important note: Register on the [AICamp Event Website](https://www.aicamp.ai/event/eventdetails/W2026071517)[ ](https://www.aicamp.ai/event/eventdetails/W2026062417)is REQUIRED for admission.

**From Code to Production - Building Production-Ready AI Agents on AWS**

The AWS Agentic AI Partner Showcase Extended features experts from **AWS, MongoDB and Mastra**, who will demonstrate how to build production-ready agentic AI systems from code to deployment. This focused session presents a complete development stack through live demonstrations, technical deep dives, and interactive discussions.

In addition to main stage tech talks and demos, partner booths will be available onsite throughout the event for attendees to visit, engage in Q&A, and deep dive into each partner's solution. The speakers will share practical insights into building, monitoring, and validating agentic AI applications that enhance your business processes and drive innovation.

**What You Will Learn:**
✔ Production-Ready Agentic AI – See live demonstrations of the complete development stack for building agentic AI systems, from coding environments through deployment and monitoring.
✔ Technical Implementation Strategies – Gain insights from AWS and partner experts on deploying agentic AI solutions with real-world use cases and AWS integration patterns.
✔ Expert Q&A & Networking – Engage directly with technical leaders from AWS and partner companies at dedicated booth stations, plus connect with fellow develope

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `8.0`

---

### Item 25 — DB id 7364

**Title:** Ingesting Agent Traces with dlthub  
**Source:** meetup  
**Location:** (none)  
**URL:** https://www.meetup.com/datatalks-meetups-global/events/314993420/

**Raw text (preview):**
```
​In this hands-on workshop, we'll show you how to stop flying blind on your AI agents. Using dltHub Pro we'll build a pipeline that ingests agent traces (e.g. tool calls, intermediate steps, token usage, and outcomes) and transforms them into structured, queryable data.

​From there, we'll turn that data into reports that actually tell you what your agents are doing, where they're failing, and how to make them better.

​**You'll learn how to:**

* ​Capture and normalize agent traces into a consistent schema
* ​Transform and model nested, variable-length trace data with dltHub Pro
* ​Deploy your pipeline and build reports that surface real insights about agent performance

​
By the end, you'll have a working reporting layer for your AI agents, so you can debug faster, optimize smarter, and ship with confidence.

​**About the speaker:**
Alena is a DevRel at dltHub. She builds and optimizes data pipelines, engages with dltHub community, and creates educational content to make data processing more accessible.

This event is sponsored by [dltHub](https://dlthub.com/?utm_source=luma)

\*\*Join our Slack: [https://datatalks.club/slack.html**](https://datatalks.club/slack.html**)
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `unknown` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.9` | content_quality: `7.5`

---

### Item 26 — DB id 7376

**Title:** CyberConnect: Virtual Career & Networking Hub for Cybersecurity Pros  
**Source:** meetup  
**Location:** Virtual  
**URL:** https://www.meetup.com/ac-sfo/events/315236665/

**Raw text (preview):**
```
Whether you're a SOC analyst, red teamer, threat intelligence expert, or just breaking into the field — **CyberConnect** is your global destination for building meaningful connections and exploring opportunities in the cybersecurity domain.

This powerful, **cybersecurity networking event online** brings together cybersecurity specialists, hiring companies, and solution providers in an unmoderated, self-managed, community-led virtual environment. Perfect for job seekers, employers, freelancers, and infosec enthusiasts alike — this event enables career growth, peer learning, and real-time knowledge sharing.

🎥 **Watch how the event works with our explainer video:**
👉 [https://www.youtube.com/watch?v=VToIVvIjIPY](https://www.youtube.com/watch?v=VToIVvIjIPY)
**💬 What to Expect at CyberConnect:**
Join a rich virtual environment where you can **chat in real time**, join discussions in group channels, or conduct **1-on-1 video conversations** to dive deeper into opportunities and collaborations.
This **online community for cybersecurity specialists** features curated channels for open conversation and focused professional engagement:

* **General** – Your orientation hub for intros, announcements, and casual conversation.
* **Intros** – Introduce yourself, your role in cybersecurity, or just share a fun fact and meet peers.
* **Networking** – Showcase your current projects, open-source contributions, or job aspirations.
* **Help Wanted** – Post or respond to open calls for SOC supp

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `unknown` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `7.5`

---

### Item 27 — DB id 7391

**Title:** July 10 - Best of CVPR (Day 3)  
**Source:** meetup  
**Location:** Online  
**URL:** https://www.meetup.com/san-francisco-the-machine-learning-conference/events/314912163/

**Raw text (preview):**
```
Welcome to the Best of CVPR series — your virtual front row to groundbreaking research, insights, and innovations from one of computer vision's premier conferences. Live from the authors to you.

**Date, Time and Location**

Jul 10, 2026
9 AM - 11 AM PT
Online. **[Register for Zoom!](https://voxel51.com/events/best-of-cvpr-july-10-2026)**

**Advancing Generative Quality and Reasoning in Multimodal AI**

This talk exposes hidden limitations of frontier multimodal models across reasoning and visual generation, demonstrates the inherent brittleness of VLMs and audio-visual MLLMs, and introduces simple yet effective techniques to build robustness. It also covers human-centric metrics for perceptually accurate evaluation of generative media.

*About the Speaker*

[Deepti Ghadiyaram](https://www.linkedin.com/in/deeptigp/) is an Assistant Professor of Computer Science at Boston University. Her research focuses on building safe, interpretable, and robust computer vision systems with advanced reasoning capabilities. Before joining BU she was at Runway and Meta AI, and earned her PhD from UT Austin in 2017.

**HyperRealm: Hyperbolic Vision Language Models for Real-World Hierarchical Multimodal Understanding**

Real-world multimodal data naturally exhibits hierarchical structure, yet standard VLMs like CLIP align images and text in Euclidean space, which cannot preserve tree-like hierarchies. HyperRealm embeds images and text in a Poincaré ball to encode hierarchical relationships, intr

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `unknown` | company_stage: `None` | spam_risk: `clean`
- deadline: `2026-07-10` | tag_confidence: `0.95` | content_quality: `8.5`

---

### Item 28 — DB id 7397

**Title:** July 8 - Best of CVPR (Day 1)  
**Source:** meetup  
**Location:** Online  
**URL:** https://www.meetup.com/san-francisco-the-machine-learning-conference/events/314911623/

**Raw text (preview):**
```
Welcome to the Best of CVPR series — your virtual front row to groundbreaking research, insights, and innovations from one of computer vision's premier conferences. Live from the authors to you.

**Date, Time and Location**

Jul 08, 2026
9 AM - 11 AM PT
Online. **[Register for Zoom!](https://voxel51.com/events/best-of-cvpr-july-8-2026)**

**Some Modalities Are More Equal Than Others: Understanding and Improving Multimodal Integration in MLLMs**

Multimodal large language models can process vision, audio, and text, but it remains unclear whether they truly integrate these modalities or rely on shortcut cues. In this talk, I will present our recent work, [“Some Modalities Are More Equal Than Others,](https://arxiv.org/abs/2511.22826)” where we introduce MMA-Bench, a benchmark designed to probe MLLMs under controlled audio–visual conflict, misleading text, and modality-specific queries. Through black-box evaluation and white-box attention analysis, we show that current MLLMs often struggle when modalities disagree, exhibit model-specific modality biases, and can be distracted by irrelevant textual context. We further propose an alignment-aware tuning strategy that trains models to answer based on the queried modality, improving robustness and multimodal grounding. This talk will highlight both the failure modes of current MLLMs and practical directions toward more reliable cross-modal reasoning.

*About the Speaker*

[Tianle Chen](https://www.linkedin.com/in/tianle-chen-1811341b

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `unknown` | company_stage: `None` | spam_risk: `clean`
- deadline: `2026-07-08` | tag_confidence: `0.95` | content_quality: `8.5`

---

### Item 29 — DB id 7398

**Title:** Building with AI: Show, Share, and Collaborate  
**Source:** meetup  
**Location:** (none)  
**URL:** https://www.meetup.com/projects/events/315449925/

**Raw text (preview):**
```
Come share your explorations in artificial intelligence.

Let's demonstrate the things we've actually built and trade hard-won tricks. Whether you're an AI engineer, a programmer, or someone who found their way in through vibe coding, there's a seat for you.

Come hear what others are working on, and show us:

* The new products and tools you've discovered.
* How you've figured out to get the most out of your coding bot.
* Your newest agentic AI workflow or automation.
* Your latest dive into machine learning — neural nets and otherwise.

And if you're looking for people to build with, you're in the right room. A few of us are hoping to find collaborators for projects.

**Please register through Zoom (one-time registration):**
[https://us02web.zoom.us/meeting/register/cU4kUPfiR0uvdlsc6Q_zrg](https://us02web.zoom.us/meeting/register/cU4kUPfiR0uvdlsc6Q_zrg)

After registering, save the Zoom link and use it to join future sessions by signing into your Zoom account.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `unknown` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.9` | content_quality: `7.0`

---

### Item 30 — DB id 7400

**Title:** The Future of Agentic Engineering and AI Workforces with Qoder  
**Source:** meetup  
**Location:** San Francisco, CA  
**URL:** https://www.meetup.com/aibuilders-sv/events/315367942/

**Raw text (preview):**
```
**Overview**
For engineering and business leaders at high-growth companies, this invite-only gathering goes beyond “which AI tool should we use?” to examine how autonomous AI workforces are moving from model to production.

Qoder, QoderWork, AI Builders, and Z.AI will bring together CTOs, VPs of Engineering, founders, and technical executives to explore how specialized AI agents can scale coding and everyday work while preserving architecture judgment, code ownership, review discipline, and security.

The session will go under the hood of Qoder Expert Mode and QoderWork’s multi-agent workflows, alongside Z AI’s GLM-5.2, a flagship model for long-horizon tasks, project-scale engineering context, and agentic coding with a 1M-token context window.

**Agenda**

* **2:00 PM** — Check-in & Pre-Networking
* **2:30 PM** — Opening Remarks
* **2:40 PM** — Qoder/QoderWork Intro and Demo — Joey Huang (Solution Architect, Qoder)
* **3:10 PM** — The Production & Ecosystem Layer — Chenyi Zhang (Member of Technical Staff, Character AI)
* **3:40 PM** — The Model Layer Perspective — Cara Li (Head of Global Ecosystem Partnerships, Z AI)
* **4:10 PM** — Open Networking
* **5:00 PM** — Event Closes

**Who Should Join**

* CEO/CTOs and Heads of Engineering deciding how AI coding should securely enter their engineering orgs.
* Senior AI Engineers and Platform Leads building next-gen AI agents looking to harness the full potential of the model layer.
* Business Leaders and Founders looking to optimi

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `8.5`

---

### Item 31 — DB id 7410

**Title:** Get Google AI Certified - AI Professionals' July 2026 Cohort  
**Source:** meetup  
**Location:** (none)  
**URL:** https://www.meetup.com/ai-professionals-san-francisco/events/315403648/

**Raw text (preview):**
```
**Free AI Professional Certification from Google: Use It, or Build a Business On It.**

Join us as we work through Google's AI Professional Certificate on Google Skills — completely free. We're working together, live, one course a week, for 7 weeks.
At the end of the 7 weeks, you'll walk away with an AI Fluent certificate from AI Professionals.

Want the actual Google AI Professional Certificate as well? Sign up for the 7-day free trial at Google Skills after we complete our 7 weeks of training.

*Note: Coursera offers the same certificate for $49 USD for the one month you need it.*

Either way, it's optional, and by week 7, you'll already know the material cold, so it's a fast finish if you choose to add it."

Whether you want to put AI to work *in* your business, or build a brand-new AI service offering *as* your business, this is the on-ramp.

**Three ways this pays off:**
**1\. Use the certificate to pivot into a career as an AI Professional\.**
Whether you are mid-career or a fresh graduate, this certificate tells potential employers that you know how to leverage AI to increase your productivity - and that you care enough to invest in your own education.

**2\. Use AI to run your business better\.**
Walk away knowing how to use Gemini, NotebookLM, and AI Studio for the stuff that eats your week: research, content, data, planning, communications. Real prompts and workflows you'll use the next morning — not theory.

**3\. Turn it into a new offering for your business\.**
T

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `ai_education`
- remote_type: `unknown` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.92` | content_quality: `8.5`

---

### Item 32 — DB id 7412

**Title:** July 10 - Best of CVPR (Day 3)  
**Source:** meetup  
**Location:** Online  
**URL:** https://www.meetup.com/san-francisco-frontier-tech-meetup/events/314912175/

**Raw text (preview):**
```
Welcome to the Best of CVPR series — your virtual front row to groundbreaking research, insights, and innovations from one of computer vision's premier conferences. Live from the authors to you.

**Date, Time and Location**

Jul 10, 2026
9 AM - 11 AM PT
Online. **[Register for Zoom!](https://voxel51.com/events/best-of-cvpr-july-10-2026)**

**Advancing Generative Quality and Reasoning in Multimodal AI**

This talk exposes hidden limitations of frontier multimodal models across reasoning and visual generation, demonstrates the inherent brittleness of VLMs and audio-visual MLLMs, and introduces simple yet effective techniques to build robustness. It also covers human-centric metrics for perceptually accurate evaluation of generative media.

*About the Speaker*

[Deepti Ghadiyaram](https://www.linkedin.com/in/deeptigp/) is an Assistant Professor of Computer Science at Boston University. Her research focuses on building safe, interpretable, and robust computer vision systems with advanced reasoning capabilities. Before joining BU she was at Runway and Meta AI, and earned her PhD from UT Austin in 2017.

**HyperRealm: Hyperbolic Vision Language Models for Real-World Hierarchical Multimodal Understanding**

Real-world multimodal data naturally exhibits hierarchical structure, yet standard VLMs like CLIP align images and text in Euclidean space, which cannot preserve tree-like hierarchies. HyperRealm embeds images and text in a Poincaré ball to encode hierarchical relationships, intr

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `unknown` | company_stage: `None` | spam_risk: `clean`
- deadline: `2026-07-10` | tag_confidence: `0.95` | content_quality: `8.5`

---

### Item 33 — DB id 7415

**Title:** R Data Science Accelerator: 1 Day Workshop in San Francisco, CA  
**Source:** eventbrite  
**Location:** San Francisco, CA  
**URL:** https://www.eventbrite.sg/e/r-data-science-accelerator-1-day-workshop-in-san-francisco-ca-tickets-1979201561148

**Raw text (preview):**
```
Master essential R workflows, analytics, and visualizations in one power-packed 1 Day data science workshop.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `ai_education`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.85` | content_quality: `5.5`

---

### Item 34 — DB id 7423

**Title:** Decrypting DeSci (Decentralized Science) | San Francisco  
**Source:** eventbrite  
**Location:** San Francisco, CA  
**URL:** https://www.eventbrite.com/e/decrypting-desci-decentralized-science-san-francisco-tickets-1647866034669

**Raw text (preview):**
```
2-hour live online training on how blockchain & Web3 are transforming research with DeSci—open, transparent & collaborative.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.85` | content_quality: `5.5`

---

### Item 35 — DB id 7434

**Title:** Intelligent Business Strategies  2 Days Workshop in  San Francisco, CA  
**Source:** eventbrite  
**Location:** San Francisco, CA  
**URL:** https://www.eventbrite.com/e/intelligent-business-strategies-2-days-workshop-in-san-francisco-ca-tickets-1991373458621

**Raw text (preview):**
```
Intelligent Business Strategies  – Learn practical ML techniques to automate tasks, improve decisions, and drive growth with Skelora.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `ai_education`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.55` | content_quality: `2.5`

---

### Item 36 — DB id 7448

**Title:** Integrating Blockchain and AI (Artificial Intelligence) | San Francisco  
**Source:** eventbrite  
**Location:** San Francisco, CA  
**URL:** https://www.eventbrite.com/e/integrating-blockchain-and-ai-artificial-intelligence-san-francisco-tickets-1968905851403

**Raw text (preview):**
```
2-hours live online training to help you navigate the convergence of Blockchain and AI (Artificial Intelligence).
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.75` | content_quality: `3.5`

---

### Item 37 — DB id 7449

**Title:** Implementation in Business | San Francisco  
**Source:** eventbrite  
**Location:** San Francisco, CA  
**URL:** https://www.eventbrite.com/e/implementation-in-business-san-francisco-tickets-1027568463937

**Raw text (preview):**
```
Learn how Artificial Intelligence can transform operations, boost efficiency, and drive industry growth!
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.7` | content_quality: `3.0`

---

### Item 38 — DB id 7451

**Title:** AI Security Intelligence Workshop 1 Day in San Francisco, CA  
**Source:** eventbrite  
**Location:** San Francisco, CA, CA  
**URL:** https://www.eventbrite.com/e/ai-security-intelligence-workshop-1-day-in-san-francisco-ca-tickets-1992618989036

**Raw text (preview):**
```
Learn how AI enhances cybersecurity through real-time monitoring, threat analysis, and risk detection with Skelora Edu Tech.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.85` | content_quality: `5.5`

---

### Item 39 — DB id 7458

**Title:** AI Skills for Healthcare: 1 Day Basic to Intermediate Course, San Francisco  
**Source:** eventbrite  
**Location:** San Francisco, CA  
**URL:** https://www.eventbrite.sg/e/ai-skills-for-healthcare-1-day-basic-to-intermediate-course-san-francisco-tickets-1978818274728

**Raw text (preview):**
```
Explore real-world AI tools, clinical applications, workflow automation, and emerging healthcare innovations in a fast-paced 1 day workshop.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.9` | content_quality: `6.0`

---

### Item 40 — DB id 7737

**Title:** Dwarkesh Unplugged, presented by WorkOS  
**Source:** luma_events  
**Location:** SFJAZZ, 201 Franklin St, San Francisco, CA 94102, USA  
**URL:** https://lu.ma/f28a739d

**Raw text (preview):**
```
Dwarkesh Unplugged, presented by WorkOS
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.45` | content_quality: `1.5`

---


## Bucket 3 — Mixed / Ambiguous (20 items, lowest tag_confidence)

### Item 41 — DB id 407

**Title:** (none)  
**Source:** hn_whoshiring  
**Location:** San Francisco, CA  
**URL:** https://news.ycombinator.com/item?id=48399489

**Raw text (preview):**
```
the post clearly mentions SF hybrid means they need someone already there.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `irrelevant` | role_type: `None` | seniority: `None`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.4` | content_quality: `2.0`

---

### Item 42 — DB id 509

**Title:** Brex Design Config After Hours  
**Source:** luma_events  
**Location:** 270 Brannan St, San Francisco, CA 94107, USA  
**URL:** https://lu.ma/bjv4dqd6

**Raw text (preview):**
```
Brex Design Config After Hours
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.4` | content_quality: `2.5`

---

### Item 43 — DB id 538

**Title:** Future Code: Rewriting the Developer Frontier  
**Source:** luma_events  
**Location:** San Francisco, CA  
**URL:** https://lu.ma/FutureCodeFrontier

**Raw text (preview):**
```
Future Code: Rewriting the Developer Frontier
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.3` | content_quality: `3.5`

---

### Item 44 — DB id 3725

**Title:** Market Manager  
**Source:** wellfound_apify_old  
**Location:** Los Angeles  
**URL:** https://wellfound.com/jobs/4420091-market-manager

**Raw text (preview):**
```
$105k – $125k
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `market manager` | seniority: `mid`
- engagement_type: `full_time` | role_category: `sales_marketing` | industry: `None`
- remote_type: `other` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.35` | content_quality: `2.0`

---

### Item 45 — DB id 3730

**Title:** Tech Recruiter  
**Source:** wellfound_apify_old  
**Location:** New York City  
**URL:** https://wellfound.com/jobs/4410738-tech-recruiter

**Raw text (preview):**
```
$150k – $180k
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `tech recruiter` | seniority: `mid`
- engagement_type: `None` | role_category: `ops_admin` | industry: `None`
- remote_type: `other` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.4` | content_quality: `1.5`

---

### Item 46 — DB id 7439

**Title:** AI Fluency Pathway - San Francisco  
**Source:** eventbrite  
**Location:** San Francisco, CA  
**URL:** https://www.eventbrite.com/e/ai-fluency-pathway-san-francisco-tickets-1991756434111

**Raw text (preview):**
```

```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `irrelevant` | role_type: `None` | seniority: `None`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.4` | content_quality: `1.0`

---

### Item 47 — DB id 7734

**Title:** The Odyssey — Early Screening (Decagon x Baseten)  
**Source:** luma_events  
**Location:** Alamo Drafthouse Cinema New Mission, 2550 Mission St, San Francisco, CA 94110, USA  
**URL:** https://lu.ma/j025zb37

**Raw text (preview):**
```
The Odyssey — Early Screening (Decagon x Baseten)
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `ai_ml`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.45` | content_quality: `2.0`

---

### Item 48 — DB id 7933

**Title:** Job Title  
**Source:** remoteok  
**Location:** Rajkot,   
**URL:** https://remoteOK.com/remote-jobs/remote-job-title-push-greece-1134371

**Raw text (preview):**
```
Tags: finance, non tech
Experience true work-â¨life harmony with hybrid working, 25 days annual leave, local bank holidays and your birthday off.<br/><br/>Please mention the word **SPLENDOR** and tag RMTk5LjgzLjIyMS4yMDY= when applying to show you read the job post completely (#RMTk5LjgzLjIyMS4yMDY=). This is a beta feature to avoid spam applicants. Companies can search these words to find applicants that read this and see they're human.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `None` | seniority: `None`
- engagement_type: `None` | role_category: `other` | industry: `fintech`
- remote_type: `other` | company_stage: `unknown` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.3` | content_quality: `1.0`

---

### Item 49 — DB id 7962

**Title:** Simple Speaker  
**Source:** remoteok  
**Location:** Ranchi,   
**URL:** https://remoteOK.com/remote-jobs/remote-simple-speaker-web-developer-ravi-one-of-the-best-in-india-1134192

**Raw text (preview):**
```
Tags: infosec, content writing, dev, web dev, digital nomad
simple speaker. <br><br>Rs.28000 p.m.<br/><br/>Please mention the word **SMILES** and tag RMTk5LjgzLjIyMS4yMDY= when applying to show you read the job post completely (#RMTk5LjgzLjIyMS4yMDY=). This is a beta feature to avoid spam applicants. Companies can search these words to find applicants that read this and see they're human.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `content writer` | seniority: `None`
- engagement_type: `None` | role_category: `other` | industry: `other`
- remote_type: `other` | company_stage: `unknown` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.3` | content_quality: `1.0`

---

### Item 50 — DB id 7965

**Title:** Executive  
**Source:** remoteok  
**Location:** Greater Aurangabad Area,   
**URL:** https://remoteOK.com/remote-jobs/remote-executive-lupin-1134194

**Raw text (preview):**
```
Tags: infosec, content writing, dev, web dev, digital nomad, education, exec
<strong>Work Experience<br><br></strong>2 to 5 years<br><br><strong>Education<br><br></strong>Graduation in Pharmacy<br><br><strong>Competencies<br><br></strong>Strategic Agility<br><br>Innovation &amp; Creativity<br><br>Customer Centricity<br><br>Developing Talent<br><br>Result Orientation<br><br>Process Excellence<br><br>Collaboration<br><br>Stakeholder Management<br/><br/>Please mention the word **MESMERIZING** and tag RMTk5LjgzLjIyMS4yMDY= when applying to show you read the job post completely (#RMTk5LjgzLjIyMS4yMDY=). This is a beta feature to avoid spam applicants. Companies can search these words to find applicants that read this and see they're human.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `executive` | seniority: `senior`
- engagement_type: `None` | role_category: `other` | industry: `other`
- remote_type: `other` | company_stage: `unknown` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.35` | content_quality: `1.5`

---

### Item 51 — DB id 7973

**Title:** Operator  
**Source:** remoteok  
**Location:** Sunderland,   
**URL:** https://remoteOK.com/remote-jobs/remote-operator-genuit-group-1134162

**Raw text (preview):**
```
Tags: supervisor, exec
N/A<br><br>Here at the Genuit Group we recognise and develop the contribution our people make to the Groupâs success and are committed to attracting talent from the widest pool. We have a role to play in making the built environment more sustainable, building a low carbon business ourselves as well as delivering sustainable solutions at scale.<br/><br/>Please mention the word **ENDEARING** and tag RMTk5LjgzLjIyMS4yMDY= when applying to show you read the job post completely (#RMTk5LjgzLjIyMS4yMDY=). This is a beta feature to avoid spam applicants. Companies can search these words to find applicants that read this and see they're human.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `operator` | seniority: `mid`
- engagement_type: `full_time` | role_category: `ops_admin` | industry: `climate_energy`
- remote_type: `other` | company_stage: `unknown` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.35` | content_quality: `1.5`

---

### Item 52 — DB id 11848

**Title:** Data Analytics AI Engineer  
**Source:** vc_portfolio  
**Location:** Tel Aviv-Yafo, Tel Aviv District, Israel  
**URL:** https://www.fireblocks.com/careers/position/4684983006?gh_jid=4684983006

**Raw text (preview):**
```
via sequoia-capital portfolio, Engineering, Analyst
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `data analytics AI engineer` | seniority: `None`
- engagement_type: `None` | role_category: `ml_ai_engineer` | industry: `ai_ml`
- remote_type: `other` | company_stage: `growth` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.35` | content_quality: `1.0`

---

### Item 53 — DB id 11936

**Title:** Applied Data Scientist / Engineer -CLT Role  
**Source:** vc_portfolio  
**Location:** Brazil - Sao Paulo  
**URL:** https://www.shift-technology.com/careers?gh_jid=4517976003

**Raw text (preview):**
```
via bessemer-ventures portfolio, Engineering
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `data scientist` | seniority: `None`
- engagement_type: `full_time` | role_category: `data_scientist` | industry: `other`
- remote_type: `other` | company_stage: `series_a_b` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.35` | content_quality: `1.5`

---

### Item 54 — DB id 12221

**Title:** Senior Software Engineer: Data Scientist  
**Source:** vc_portfolio  
**Location:**  India (Office),  Panchshil , Pune , India  
**URL:** https://cohesity.wd5.myworkdayjobs.com/Cohesity_Careers/job/Pune---Panchshil---India-Office/Senior-Software-Engineer--Data-Scientist_R03110

**Raw text (preview):**
```
via gv portfolio, $5000-$4500000/Year, Engineering
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `senior software engineer` | seniority: `senior`
- engagement_type: `full_time` | role_category: `software_engineer` | industry: `other`
- remote_type: `other` | company_stage: `unknown` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.35` | content_quality: `1.0`

---

### Item 55 — DB id 13398

**Title:** Resource mobiliser  
**Source:** remoteok  
**Location:** Mathura,   
**URL:** https://remoteOK.com/remote-jobs/remote-resource-mobiliser-vrindavan-chandrodaya-mandir-1134372

**Raw text (preview):**
```
Tags: finance, non tech, engineer
Engineering, Commerce, Finance etc. all have a role to play<br/><br/>Please mention the word **THOUGHTFULNESS** and tag RMTk5LjgzLjIyMS4yMDY= when applying to show you read the job post completely (#RMTk5LjgzLjIyMS4yMDY=). This is a beta feature to avoid spam applicants. Companies can search these words to find applicants that read this and see they're human.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `resource mobiliser` | seniority: `None`
- engagement_type: `None` | role_category: `sales_marketing` | industry: `other`
- remote_type: `other` | company_stage: `unknown` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.35` | content_quality: `1.5`

---

### Item 56 — DB id 25420

**Title:** Staff Data Engineer  
**Source:** vc_portfolio  
**Location:** India Bengaluru, Karnataka, India  
**URL:** https://servicetitan.wd1.myworkdayjobs.com/ServiceTitan/job/India-Bengaluru-Karnataka/Staff-Data-Engineer_JR114925

**Raw text (preview):**
```
via sequoia-capital portfolio, Engineering
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `data engineer` | seniority: `staff+`
- engagement_type: `None` | role_category: `data_engineer` | industry: `other`
- remote_type: `other` | company_stage: `growth` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.35` | content_quality: `1.0`

---

### Item 57 — DB id 25426

**Title:** Data Engineer  
**Source:** vc_portfolio  
**Location:** United States  
**URL:** https://jobs.jobvite.com/versa-networks/job/oHh8wfwm?nl=1&fr=true

**Raw text (preview):**
```
via sequoia-capital portfolio, $150000-$220000/Year, remote, Engineering
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `data engineer` | seniority: `mid`
- engagement_type: `full_time` | role_category: `data_engineer` | industry: `other`
- remote_type: `other` | company_stage: `series_a_b` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.4` | content_quality: `1.5`

---

### Item 58 — DB id 25468

**Title:** Machine Learning Engineer - All Levels  
**Source:** vc_portfolio  
**Location:** Auckland, North Island, New Zealand, Auckland  
**URL:** https://jobs.ashbyhq.com/halter/2e8cf3ec-3a67-405a-ac71-271f22ae3f74

**Raw text (preview):**
```
via bessemer-ventures portfolio, Engineering
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `machine learning engineer` | seniority: `mid`
- engagement_type: `full_time` | role_category: `ml_ai_engineer` | industry: `other`
- remote_type: `other` | company_stage: `series_a_b` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.35` | content_quality: `1.0`

---

### Item 59 — DB id 25488

**Title:** Research Scientist  
**Source:** vc_portfolio  
**Location:** San Francisco Bay Area  
**URL:** https://drive.google.com/file/d/1hkzu5jWtdC1wytoC1kTYOrFb9Uw-cJKL/view

**Raw text (preview):**
```
via bessemer-ventures portfolio, $70000-$240000/Year, remote, Science
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `job` | role_type: `research scientist` | seniority: `mid`
- engagement_type: `full_time` | role_category: `data_scientist` | industry: `science`
- remote_type: `hyperlocal_sf` | company_stage: `series_a_b` | spam_risk: `suspicious`
- deadline: `None` | tag_confidence: `0.4` | content_quality: `1.5`

---

### Item 60 — DB id 25553

**Title:** [AI 웨비나] Data Engineer/Data Analytics Engineer  
**Source:** vc_portfolio  
**Location:** Seoul  
**URL:** https://toss.im/career/job-detail?gh_jid=7725514003

**Raw text (preview):**
```
via bessemer-ventures portfolio, Engineering
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- role_type: `____________`
- seniority (intern/junior/mid/senior/staff/lead/exec/n/a): `____________`
- engagement_type (full_time/part_time/contract/internship/n/a): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `event` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `ai_ml`
- remote_type: `other` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.45` | content_quality: `2.0`

---


## Bucket 4 — Networking (20 items, random sample)

### Item 61 — DB id 350

**Title:** (none)  
**Source:** hn_whoshiring  
**Location:** (none)  
**URL:** https://news.ycombinator.com/item?id=48398657

**Raw text (preview):**
```
I would love to chat about how I could help your mission. I'm an independent software developer that has spent my entire career working in waste. Former VP of Engineering at Routeware and now doing consulting with haulers to achieve exactly what you describe here: business process automation with agentic solutions. My current project (https://getklau.com) is all about wrapping roll-off dispatching with agentic tools to help dispatchers make better decisions and drive more value (disposal arbitrage is the big unlock here).
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `None`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `unknown` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.75` | content_quality: `2.0`

---

### Item 62 — DB id 355

**Title:** (none)  
**Source:** hn_whoshiring  
**Location:** (none)  
**URL:** https://news.ycombinator.com/item?id=48378200

**Raw text (preview):**
```
Hey,8+ years of full-stack product experience, including fintech and consumer apps!Previously been an early engineer at 2x companies which are unicorns now, and another, which got acquired by Cloudflare (most single-handedly built an entire mobile platform from zero to one)My email is: irohitbhatia@gmail.comNot sure how to drop DM on Hacker News
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `senior`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `unknown` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.7` | content_quality: `3.0`

---

### Item 63 — DB id 406

**Title:** (none)  
**Source:** hn_whoshiring  
**Location:** India  
**URL:** https://news.ycombinator.com/item?id=48399120

**Raw text (preview):**
```
I'm AI engineer with hands on 2 years of experience and looking for an opportunity as an AI engineer role at your organization 
Location : india
Willing to relocate : yes
remote : Open to work remotlyResume : https://drive.google.com/file/d/17S6IGlKVqvQdmsbF7PS_j5NNPMT...
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `AI engineer` | seniority: `junior`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `other` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.75` | content_quality: `3.5`

---

### Item 64 — DB id 462

**Title:** (none)  
**Source:** hn_whoshiring  
**Location:** (none)  
**URL:** https://news.ycombinator.com/item?id=48459128

**Raw text (preview):**
```
I'm AI Engineer hands on 2 Years of experience fully AGentic frame works, LLM Models, RAG, Vector DBInterested to join your organization very activelyResume : https://drive.google.com/file/d/16qqv3NYPT94RbZU2amubO_AK7yl...
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `AI engineer` | seniority: `junior`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `unknown` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.7` | content_quality: `3.5`

---

### Item 65 — DB id 487

**Title:** (none)  
**Source:** hn_whoshiring  
**Location:** Poland / EU  
**URL:** https://news.ycombinator.com/item?id=48518968

**Raw text (preview):**
```
SEEKING WORK | Poland / EU | Remote CET | Senior Full Stack DeveloperSenior Full Stack Developer / Team Lead with 10+ years of experience.
Stack: React, TypeScript, Python, Django, Node.js, PostgreSQL, Docker/Kubernetes, Azure.
Strong in SaaS platforms, APIs, dashboards, admin panels, production debugging, integrations and delivery ownership.Available for: short-term contract, part-time, full-time B2B, project rescue, production support.
Can start immediately.LinkedIn: https://www.linkedin.com/in/dmitriy-kostenko/
CV: https://drive.google.com/file/d/1l8AIB9WLnBy4R1RnBTnGLax1diP...
Email: dmitriy.finswim@gmail.com
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `other` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.9` | content_quality: `1.5`

---

### Item 66 — DB id 488

**Title:** (none)  
**Source:** hn_whoshiring  
**Location:** Dakshina Kannada, Karnataka, India  
**URL:** https://news.ycombinator.com/item?id=48531236

**Raw text (preview):**
```
Location: Dakshina Kannada, Karnataka, India Remote: Yes (IST overlap) Willing to relocate: Within India for strong opportunities Technologies: SIEM monitoring, Splunk ES/SOAR, log analysis, threat hunting, incident response basics, vulnerability assessment, penetration testing, digital forensics, AWS security, IAM, Secrets Manager, Linux, Python, Docker, Git, network security Résumé/CV: https://drive.google.com/drive/folders/1KGUmGsSffOLFiFCdzrKj...
Email: www.giridharpai@gmail.com
Cybersecurity graduate seeking Information Security Analyst, Cyber Security Analyst, Penetration Tester, or SOC Analyst roles.I have hands-on experience in information security, penetration testing, and SOC operations. I’ve worked with Splunk SIEM monitoring, threat hunting, vulnerability assessment, digital forensics, and incident response fundamentals. I’m ranked in the top 1% on TryHackMe with 13 certifica

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `junior`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `other` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.85` | content_quality: `2.0`

---

### Item 67 — DB id 507

**Title:** Our Agentic Future: An Evening of Networking & Discussion on Intelligent Finance  
**Source:** luma_events  
**Location:** San Francisco, CA  
**URL:** https://lu.ma/54qrpne7

**Raw text (preview):**
```
Our Agentic Future: An Evening of Networking & Discussion on Intelligent Finance
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.7` | content_quality: `6.5`

---

### Item 68 — DB id 513

**Title:** After Hours: Dim Sum & Mahjong  
**Source:** luma_events  
**Location:** San Francisco, CA  
**URL:** https://lu.ma/mahjong-night

**Raw text (preview):**
```
After Hours: Dim Sum & Mahjong
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.7` | content_quality: `2.0`

---

### Item 69 — DB id 525

**Title:** Sentry x GLITCHED & GGWP - Women in Game Dev Meetup  
**Source:** luma_events  
**Location:** Sentry, 45 Fremont St, San Francisco, CA 94105, USA  
**URL:** https://lu.ma/dqsp2d17

**Raw text (preview):**
```
Sentry x GLITCHED & GGWP - Women in Game Dev Meetup
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.75` | content_quality: `2.0`

---

### Item 70 — DB id 541

**Title:** Extraordinary Founders Dinner (hosted by Andrew Yeung)  
**Source:** luma_events  
**Location:** San Francisco, CA  
**URL:** https://lu.ma/extraordinarydinnersf

**Raw text (preview):**
```
Extraordinary Founders Dinner (hosted by Andrew Yeung)
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `None`
- deadline: `None` | tag_confidence: `0.55` | content_quality: `3.5`

---

### Item 71 — DB id 7402

**Title:** Bay Area AI War Room - Berkeley Edition - Saturday, 10:00 AM  
**Source:** meetup  
**Location:** Berkeley, CA  
**URL:** https://www.meetup.com/bay-area-artificial-war-room/events/313150510/

**Raw text (preview):**
```
Models, agent, systems, ethics, the law, business, art and impact we discuss it all. With the DeepSeek hoopla fading, what of Reasoning models?

Inspired by the Berkeley AI War Room, we invite you to join us at the same venue, same time, and with the same dynamic community.

Come share your interests, showcase your projects, and discuss the latest trends and news that's shaping the AI landscape at a rapid pace.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `bay_area` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.9` | content_quality: `6.5`

---

### Item 72 — DB id 7447

**Title:** Startup Tech & AI Networking in San Francisco  
**Source:** eventbrite  
**Location:** San Francisco, CA  
**URL:** https://www.eventbrite.com/e/startup-tech-ai-networking-in-san-francisco-tickets-1992503678138

**Raw text (preview):**
```
Dive into tech with other professionals! Network and build strong relationships with investors, tech experts, and entrepreneurs in SF.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.85` | content_quality: `4.5`

---

### Item 73 — DB id 7669

**Title:** (none)  
**Source:** hn_whoshiring  
**Location:** United States of America (MST)  
**URL:** https://news.ycombinator.com/item?id=48754418

**Raw text (preview):**
```
full-disclosure: i am ex-homeless transitioning from living on the streets to being a participant in society again...  Location: United States of America _MST_
  Remote: No
  Willing to relocate: Yes
  Technologies: Irrelevant, but Typescript, Javacript, React, GraphQL, .etc
  Resume: https://fur-tea-laser.github.io/resume/
  Email: fur.tea.laser@gmail.com

I'm a quasi-mathematician who adapts and translates rigorous, nuanced mathematical concepts for more expressive mediums like natural language and code. This results in shared processes for synthesizing and analyzing technical assets that are actionable, pragmatic, and accessible to both deep technical experts and practical execution teams alike.Think of me as an LLM wrangler who uses latent space acupuncture to pin down precise model behaviors, replacing haphazard reactions with a systematized, consistent iterative process.Let's chat!
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `unknown` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.75` | content_quality: `4.0`

---

### Item 74 — DB id 7725

**Title:** Open Studios: Clothing Swap & Headshots for Women & Femmes  
**Source:** luma_events  
**Location:** Brave New Spaces, 447 Minna St, San Francisco, CA 94103, USA  
**URL:** https://lu.ma/4j0nln17

**Raw text (preview):**
```
Fast fashion wants you consuming alone. We're doing the opposite.
Join us at Brave New Spaces for an afternoon of swapping, sipping, and connecting - because the future of fashion is circular, and the future of community is us.
Bring up to 5-10 gently loved pieces from your closet or jewelry. Leave with something new-to-you, a fresh look, and a room full of women who get it.
What's included:
Clothing swap floor open all afternoon
Complimentary drinks (alcoholic for 21+ and non-alcoholic)
Yummy bites
DJ sets by Vieux Carré
Headshots by Melissa de Mata
Good energy, better company
✨Community Hosts✨
Events Wizard, @ginamariko
Cannabis & Fashion Queen, @nina_parks
Musical Selector, @dj_vieux_carre
Portrait Photographer, @melissademata
Bring clothes to swap. All women and femmes welcome.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.95` | content_quality: `7.0`

---

### Item 75 — DB id 7732

**Title:** Researcher Game Night - Applied Compute  
**Source:** luma_events  
**Location:** San Francisco, CA  
**URL:** https://lu.ma/09gobnrc

**Raw text (preview):**
```
Researcher Game Night - Applied Compute
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.55` | content_quality: `2.0`

---

### Item 76 — DB id 7738

**Title:** Scaling revenue at Stripe and Vercel with Jeanne DeWitt Grosser (COO, Vercel)  
**Source:** luma_events  
**Location:** San Francisco, CA  
**URL:** https://lu.ma/7h2hjufc

**Raw text (preview):**
```
Scaling revenue at Stripe and Vercel with Jeanne DeWitt Grosser (COO, Vercel)
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `hyperlocal_sf` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.75` | content_quality: `3.0`

---

### Item 77 — DB id 23528

**Title:** Join our Talent Community!  
**Source:** greenhouse  
**Location:** Global  
**URL:** https://www.cockroachlabs.com/careers/job/?gh_jid=2578081

**Raw text (preview):**
```
Curious what it's like to work at Cockroach Labs?  Check out our 
company guide
 to learn more!


The swarm keeps growing here at Cockroach Labs. We regularly update our careers page to reflect the current open positions, but we are expecting major growth coming off the most recent Series F funding so there are many new roles on the horizon.  If you don't see a position open right now that's a fit but you are still interested in the work we're doing, please apply via the button above and the Recruiting team will keep you in mind for future opportunities.  You also have the option to opt into our Recruiting newsletter, which will keep you informed of the latest happenings related to hiring. 


Thanks for your interest in Cockroach Labs!  If any questions come up, feel free to drop us a line at applications@cockroachlabs.com.


 


#LI-DNI
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `other` | company_stage: `growth` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.75` | content_quality: `4.0`

---

### Item 78 — DB id 33103

**Title:** Join Our Talent Network  
**Source:** greenhouse  
**Location:** Remote  
**URL:** https://job-boards.greenhouse.io/midihealth/jobs/4412523005

**Raw text (preview):**
```
Interested in Midi, but haven't found an open role that suits you? We invite you to join our Talent Network so we can stay connected. At Midi, we're always on the lookout for exceptional talent to enhance our team.


By joining our Talent Network, you can expect the following benefits:




Opportunities for Future Roles
: We'll notify you about new openings that may be a good match for your skills and interests.


Stay up-to-date about Midi Health
: Receive occasional emails about Midi Health, what we're up to and more in-depth looks into the impacts we're creating




If you're unsure about whether you're a fit for Midi, we encourage you to join our Talent Network anyway! It's a commitment-free way to explore potential opportunities, and you can opt out at any time if you decide it's not for you.


By providing your phone number you consent to possible be texted in relation to jobs that

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `health_general`
- remote_type: `remote` | company_stage: `unknown` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.85` | content_quality: `6.5`

---

### Item 79 — DB id 33804

**Title:** Customer Council  
**Source:** greenhouse  
**Location:** Berlin  
**URL:** https://traderepublic.com/en-de/customer-council?gh_jid=7699879003

**Raw text (preview):**
```
Work together with our Management Team to shape the future of Trade Republic. Apply now.
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `other` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.7` | content_quality: `3.0`

---

### Item 80 — DB id 35377

**Title:** Don’t See the Right Role? Join Our Talent Community  
**Source:** greenhouse  
**Location:** New York, NY  
**URL:** https://job-boards.greenhouse.io/pelago/jobs/5063783007

**Raw text (preview):**
```
Pelago is the leading specialty substance use care provider, built on the belief that effective treatment means matching care intensity to what each member actually needs rather than defaulting to the most expensive intervention. Our programs guide members through every stage of the substance use spectrum, from unhealthy habits to active use disorders, delivering personalized treatment for tobacco, alcohol, opioid, cannabis, and stimulant use based on individual health, habits, genetics, and goals.


With Sona, our voice-first AI Mental Health Specialist, Pelago now applies that same clinically-driven model to mental health, pairing deep clinical expertise with technology to expand access without compromising care quality. We believe technology should make clinical care more precise and more human, not replace the judgment behind it.


Pelago has scaled to helping hundreds of employers a

[...truncated, see url for full posting...]
```

**Human Tag (fill in):**
- category (job / event / networking / irrelevant): `____________`
- is this classification correct? (Y/N): `____________`
- notes: `____________`

**Auto-Tagged (system output):**
- category: `networking` | role_type: `None` | seniority: `n/a`
- engagement_type: `None` | role_category: `None` | industry: `None`
- remote_type: `other` | company_stage: `None` | spam_risk: `clean`
- deadline: `None` | tag_confidence: `0.85` | content_quality: `6.0`

---
