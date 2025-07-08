# Merge Instructions for PDF RAG Feature

## Feature Branch: `s03-assignment`

This branch adds PDF upload and RAG (Retrieval-Augmented Generation) functionality to the Aethon chat application.

## Changes Summary

- **Backend**: Added PDF upload, text extraction, vector indexing, and RAG-enhanced chat
- **Frontend**: Added PDF upload UI with controls to toggle PDF context
- **Dependencies**: Added `aimakerspace`, `pypdf2`, `numpy`, and `faiss-cpu`
- **Documentation**: Created comprehensive PDF RAG usage guide

## Merge Instructions

### Option 1: GitHub Pull Request (Recommended)

1. Push the branch to GitHub:
   ```bash
   git push origin s03-assignment
   ```

2. Go to your GitHub repository

3. Click "Compare & pull request" for the `s03-assignment` branch

4. Review the changes and create the PR with title:
   ```
   feat: Add PDF upload and RAG functionality
   ```

5. Add description:
   ```
   This PR adds the ability to upload PDF documents and chat with their contents using RAG technology.
   
   - Users can upload PDFs through the web interface
   - PDFs are indexed using vector embeddings
   - Chat responses can include relevant information from the PDF
   - Aethon maintains its personality while answering from documents
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
   git push origin s03-assignment
   
   # Create PR
   gh pr create --title "feat: Add PDF upload and RAG functionality" \
     --body "This PR adds the ability to upload PDF documents and chat with their contents using RAG technology." \
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
   git merge s03-assignment
   ```

3. Push to remote:
   ```bash
   git push origin main
   ```

## Post-Merge Steps

1. **Deploy to Vercel**: The merge will trigger automatic deployment

2. **Verify Environment Variables**: Ensure these are set in Vercel:
   - `OPENAI_API_KEY`
   - `LANGFUSE_PUBLIC_KEY`
   - `LANGFUSE_SECRET_KEY`

3. **Test the Feature**:
   - Upload a test PDF
   - Ask questions about its content
   - Verify Aethon maintains personality while using PDF context

## Rollback Plan

If issues arise after merge:

```bash
# Find the commit before the merge
git log --oneline

# Revert to previous commit
git revert -m 1 <merge-commit-hash>
git push origin main
``` 