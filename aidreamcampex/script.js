class GitHub {
  constructor() {
    this.baseUrl = 'https://api.github.com/users/';
    this.reposCount = 5;
    this.reposSort = 'created: asc';
  }

  async getUser(username) {
    const [profileRes, reposRes] = await Promise.all([
      fetch(`${this.baseUrl}${username}`),
      fetch(`${this.baseUrl}${username}/repos?per_page=${this.reposCount}&sort=${this.reposSort}`)
    ]);
    const profile = await profileRes.json();
    const repos   = await reposRes.json();
    return { profile, repos };
  }
}

class UI {
  constructor() {
    this.profile  = document.getElementById('profile');
    this.alertBox = document.getElementById('alert');
  }

  showSpinner() {
    this.profile.innerHTML = `
      <div class="text-center my-5">
        <div class="spinner-border text-primary" role="status">
          <span class="sr-only">Loading...</span>
        </div>
      </div>
    `;
  }

  showProfile(user) {
    this.alertBox.innerHTML = '';
    this.profile.innerHTML = `
      <div class="card mb-4">
        <div class="row no-gutters">
          <div class="col-md-3 text-center p-3">
            <img src="${user.avatar_url}" class="img-fluid rounded-circle mb-2" />
            <a href="${user.html_url}" target="_blank" class="btn btn-primary btn-block">
              View Profile
            </a>
          </div>
          <div class="col-md-9">
            <div class="card-body">
              <span class="badge badge-primary">Public Repos: ${user.public_repos}</span>
              <span class="badge badge-secondary">Public Gists: ${user.public_gists}</span>
              <span class="badge badge-success">Followers: ${user.followers}</span>
              <span class="badge badge-info">Following: ${user.following}</span>
              <ul class="list-group mt-3">
                <li class="list-group-item">Company: ${user.company || 'N/A'}</li>
                <li class="list-group-item">
                  Website/Blog:
                  ${user.blog
                    ? `<a href="${user.blog}" target="_blank">${user.blog}</a>`
                    : 'N/A'}
                </li>
                <li class="list-group-item">Location: ${user.location || 'N/A'}</li>
                <li class="list-group-item">
                  Member Since: ${new Date(user.created_at).toLocaleDateString()}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      <h4 class="mb-3">Latest Repos</h4>
      <div id="repos"></div>
    `;
  }

  showRepos(repos) {
    const repoList = repos
      .map(repo => `
        <div class="card card-body mb-2">
          <div class="row">
            <div class="col-md-6">
              <a href="${repo.html_url}" target="_blank">${repo.name}</a>
            </div>
            <div class="col-md-6 text-right">
              <span class="badge badge-primary">Stars: ${repo.stargazers_count}</span>
              <span class="badge badge-secondary">Watchers: ${repo.watchers_count}</span>
              <span class="badge badge-success">Forks: ${repo.forks_count}</span>
            </div>
          </div>
        </div>
      `)
      .join('');
    document.getElementById('repos').innerHTML = repoList;
  }

  showAlert(msg, cls = 'alert-danger') {
    this.alertBox.innerHTML = `<div class="alert ${cls}">${msg}</div>`;
    setTimeout(() => (this.alertBox.innerHTML = ''), 3000);
  }

  clearProfile() {
    this.profile.innerHTML = '';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const github    = new GitHub();
  const ui        = new UI();
  const searchInp = document.getElementById('searchUser');

  searchInp.addEventListener('keyup', e => {
    const username = e.target.value.trim();
    if (!username) {
      ui.clearProfile();
      return;
    }

    ui.showSpinner();
    github
      .getUser(username)
      .then(data => {
        if (data.profile.message === 'Not Found') {
          ui.clearProfile();
          ui.showAlert('User not found', 'alert-warning');
        } else {
          ui.showProfile(data.profile);
          ui.showRepos(data.repos);
        }
      })
      .catch(() => {
        ui.clearProfile();
        ui.showAlert('네트워크 오류가 발생했습니다.', 'alert-danger');
      });
  });
});
