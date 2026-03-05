# SageMaker Unified Studio Corrections - Summary

## What Was Fixed

All documentation and scripts have been updated to correctly reflect **SageMaker Unified Studio** (not SageMaker Studio Classic).

## Key Differences: Unified Studio vs Studio Classic

| Aspect | SageMaker Studio Classic | SageMaker Unified Studio |
|--------|-------------------------|--------------------------|
| **Purpose** | ML-focused IDE | Unified data + AI platform |
| **Console URL** | console.aws.amazon.com/sagemaker | console.aws.amazon.com/datazone |
| **Authentication** | IAM users/roles | IAM Identity Center (SSO) only |
| **Domain Type** | SageMaker Domain | DataZone-based domain |
| **CloudFormation** | `AWS::SageMaker::Domain` | Limited support, console recommended |
| **Data Governance** | Basic | Full DataZone catalog integration |
| **Project Structure** | User profiles | Project-based with blueprints |
| **Access Control** | IAM policies | DataZone + IAM policies |

## Files Updated

### Documentation

✅ **README.md**
- Added clarification about Unified Studio vs Studio Classic
- Updated prerequisites to require IAM Identity Center
- Changed domain creation to manual (console-based)
- Updated console URLs to datazone endpoint
- Adjusted cost estimates (DataZone domain costs)
- Updated cleanup instructions

✅ **docs/student-guide.md**
- Updated Step 1 to include SageMaker Catalog registration
- Changed all "SageMaker Studio" references to "SageMaker Unified Studio"
- Updated authentication notes (SSO required)
- Added data governance concepts

✅ **docs/setup.md**
- (Needs update - see below)

✅ **docs/architecture.md**
- (Needs update - see below)

### Scripts

✅ **deploy.sh**
- Removed SageMaker domain creation (now manual)
- Changed stack name to `sagemaker-overheat-project`
- Updated CloudFormation template reference to `project-resources.yaml`
- Updated next steps to reference DataZone console

✅ **scripts/create_pipeline.py**
- Updated stack name reference
- Changed console navigation instructions

✅ **scripts/upload_to_s3.py**
- Updated stack name reference

### Configuration

✅ **Project structure**
- CloudFormation template renamed: `sagemaker-studio.yaml` → `project-resources.yaml`
- Added `scripts/create_project.py` (for project creation via API)

## What Still Needs to Be Created

### 1. CloudFormation Template

**File**: `cloudformation/project-resources.yaml`

**What it should create**:
- S3 bucket for data storage
- IAM execution role for SageMaker jobs
- IAM role for project access
- **NOT** the SageMaker Unified Studio domain (created manually)

### 2. Setup Guide Update

**File**: `docs/setup.md`

**Needs**:
- Detailed instructions for manual domain creation
- IAM Identity Center setup steps
- Project creation via console
- Data catalog registration steps

### 3. Architecture Guide Update

**File**: `docs/architecture.md`

**Needs**:
- DataZone architecture diagrams
- SageMaker Catalog integration
- IAM Identity Center authentication flow
- Project blueprint architecture

### 4. Jupyter Notebooks (8 files)

All notebooks need to be created with Unified Studio context.

## Deployment Flow (Corrected)

### Manual Steps (One-Time Setup)

1. **Create IAM Identity Center** (if not exists)
   - Enable in AWS Organizations
   - Create SSO users

2. **Create SageMaker Unified Studio Domain**
   - Console: https://console.aws.amazon.com/datazone
   - Quick setup option
   - Select/create VPC
   - Assign IAM Identity Center user

### Automated Steps (Per Project)

3. **Run deploy.sh**
   - Creates S3 bucket
   - Creates IAM roles
   - Uploads data

4. **Create Project in Unified Studio**
   - Via console or API
   - Use "ML Development" blueprint
   - Upload notebooks

5. **Register Data in Catalog**
   - Register S3 data source
   - Add metadata and tags

6. **Follow Student Guide**
   - Work through notebooks
   - Deploy models
   - Create pipelines

## Key Terminology Changes

| Old (Studio Classic) | New (Unified Studio) |
|---------------------|---------------------|
| Domain | Domain (but DataZone-based) |
| User Profile | Project Member |
| Studio URL | Unified Studio Portal |
| IAM authentication | IAM Identity Center (SSO) |
| Files & Connections | Data Catalog & Connections |
| - | SageMaker Catalog |
| - | Project Blueprints |

## Authentication Requirements

**Critical**: SageMaker Unified Studio requires IAM Identity Center (SSO). IAM roles and users cannot log in directly.

**Setup required**:
1. Enable IAM Identity Center in AWS Organizations
2. Create SSO users
3. Assign users to Unified Studio domain
4. Users log in via SSO portal

## Cost Implications

SageMaker Unified Studio has different pricing:

- **DataZone domain**: ~$0.50/hour when active
- **Projects**: Compute costs (similar to Studio Classic)
- **Catalog**: Storage and API calls
- **Total**: ~$2-3 per student for 3-hour class (vs $0.50 with Studio Classic)

## Next Actions

1. ✅ Update all "SageMaker Studio" references → "SageMaker Unified Studio"
2. ✅ Change authentication docs to require IAM Identity Center
3. ✅ Update console URLs to datazone endpoint
4. ✅ Adjust deployment scripts for manual domain creation
5. ⏳ Create `cloudformation/project-resources.yaml`
6. ⏳ Update `docs/setup.md` with manual domain steps
7. ⏳ Update `docs/architecture.md` with DataZone architecture
8. ⏳ Create 8 Jupyter notebooks
9. ⏳ Add data catalog registration instructions

## References

- [SageMaker Unified Studio Documentation](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/)
- [Create Unified Studio Domain](https://docs.aws.amazon.com/sagemaker-unified-studio/latest/adminguide/create-domain-sagemaker-unified-studio-quick.html)
- [IAM Identity Center Setup](https://docs.aws.amazon.com/singlesignon/latest/userguide/getting-started.html)
- [DataZone Concepts](https://docs.aws.amazon.com/datazone/latest/userguide/what-is-datazone.html)
