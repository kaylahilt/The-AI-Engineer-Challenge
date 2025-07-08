# Merge Instructions for Named Entity Extraction Feature

## Feature Branch: `feature/named-entity-extraction`

This branch adds named entity extraction functionality to the PDF upload feature, allowing users to see the top 5 most mentioned entities (people, organizations, locations) from their uploaded PDFs.

## Changes Summary

### Frontend Changes
- Added checkbox to enable/disable entity extraction before uploading PDF
- Updated state management to handle entity data
- Added UI section to display top 5 named entities with labels and counts
- Added CSS styling for entity display with proper visual hierarchy

### Backend Changes
- Integrated spaCy NLP library for entity extraction
- Added `extract_named_entities` method to PDFHandler class
- Modified upload endpoint to handle entity extraction parameter
- Filters out common entity types (dates, numbers, etc.) to focus on meaningful entities

### Dependencies Added
- `spacy>=3.0.0` - NLP library for entity recognition
- `en-core-web-sm` - English language model for spaCy

## Merge Instructions

### Option 1: GitHub Pull Request (Recommended)

1. Push the branch to GitHub:
   ```bash
   git push origin feature/named-entity-extraction
   ```

2. Go to your GitHub repository

3. Click "Compare & pull request" for the `feature/named-entity-extraction` branch

4. Review the changes and create the PR with title:
   ```
   feat: Add named entity extraction to PDF uploads
   ```

5. Add description:
   ```
   This PR adds the ability to extract and display named entities from uploaded PDFs.
   
   Features:
   - Users can choose to extract entities via checkbox before upload
   - Top 5 most frequent entities are displayed (people, orgs, locations)
   - Entity type and occurrence count shown for each entity
   - Graceful fallback if spaCy is unavailable
   
   Technical details:
   - Uses spaCy for NLP processing
   - Filters out dates, numbers, and other non-meaningful entities
   - Entity extraction is optional to avoid slowing down uploads
   ```

6. Merge the PR after review

### Option 2: GitHub CLI

1. Install GitHub CLI if not already installed:
   ```bash
   brew install gh  # macOS
   ```

2. Create and merge the PR:
   ```bash
   # Push the branch
   git push origin feature/named-entity-extraction
   
   # Create PR
   gh pr create --title "feat: Add named entity extraction to PDF uploads" \
     --body "This PR adds the ability to extract and display named entities from uploaded PDFs using spaCy NLP." \
     --base main
   
   # After review, merge
   gh pr merge --merge
   ```

### Option 3: Local Merge (Not Recommended for Production)

1. Switch to main branch:
   ```bash
   git checkout main
   ```

2. Merge the feature branch:
   ```bash
   git merge feature/named-entity-extraction
   ```

3. Push to remote:
   ```bash
   git push origin main
   ```

## Post-Merge Steps

1. **Deploy to Vercel**: The merge will trigger automatic deployment

2. **Verify spaCy Installation**: The deployment may take longer due to spaCy installation

3. **Test the Feature**:
   - Check the "Extract named entities" checkbox
   - Upload a PDF with recognizable entities (people, organizations, locations)
   - Verify top 5 entities appear below the upload confirmation
   - Test without checkbox to ensure normal upload still works

## Rollback Plan

If issues arise after merge:

```bash
# Find the commit before the merge
git log --oneline

# Revert to previous commit
git revert -m 1 <merge-commit-hash>
git push origin main
```

## Known Limitations

- Entity extraction adds processing time to uploads
- Limited to English language documents (en_core_web_sm model)
- May not catch all entities depending on document formatting
- Vercel deployment size may increase due to spaCy dependencies 