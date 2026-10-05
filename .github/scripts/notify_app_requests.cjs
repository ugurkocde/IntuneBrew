/** Deliver request notices idempotently; acknowledge only completed deliveries. */
async function notifyRequests({ github, owner, repo, notifications, log = console.log }) {
  const delivered = [];
  for (const item of notifications) {
    const issue = { owner, repo, issue_number: item.issue };
    try {
      const comments = await github.paginate(github.rest.issues.listComments, { ...issue, per_page: 100 });
      const alreadySent = comments.some(comment => comment.user?.login === 'github-actions[bot]' && comment.body?.includes(item.marker));
      if (!alreadySent) {
        let body;
        if (item.kind === 'live') {
          body = '## Now live\n\nThe requested apps below are available in the catalog.\n\n';
          body += '| App | Version |\n|-----|---------|\n';
          for (const app of item.apps) body += `| ${app.name} | \`${app.version}\` |\n`;
          body += '\n[Browse the catalog](https://www.intunebrew.com/apps). Allow a few minutes for the website to refresh.\n';
          if (item.needs_review) body += '\nOther parts of this request still need maintainer review, so the issue remains open.\n';
        } else {
          body = '## Build needs review\n\nThese requested casks have not reached the catalog after three days:\n\n';
          for (const cask of item.missing) body += `- \`${cask}\`\n`;
          body += '\nThe request remains tracked. A maintainer should inspect collection/packaging failures; a later successful build will still send a completion notice.\n';
        }
        await github.rest.issues.createComment({ ...issue, body: `${body}\n${item.marker}` });
      }
      if (item.kind === 'live' && !item.needs_review) {
        await github.rest.issues.removeLabel({ ...issue, name: 'needs-review' }).catch(error => {
          if (error.status !== 404) throw error;
        });
        await github.rest.issues.update({ ...issue, state: 'closed', state_reason: 'completed' });
      } else {
        await github.rest.issues.addLabels({ ...issue, labels: ['needs-review'] });
        await github.rest.issues.update({ ...issue, state: 'open' });
      }
      delivered.push(item);
    } catch (error) {
      log(`Notification for #${item.issue} will be retried: ${error.message}`);
    }
  }
  return delivered;
}
module.exports = { notifyRequests };
