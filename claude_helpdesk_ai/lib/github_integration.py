# -*- coding: utf-8 -*-
# Part of Claude AI Helpdesk Automation. See LICENSE file for full copyright and licensing details.

import base64
import logging
import re
from urllib.parse import urlparse

_logger = logging.getLogger(__name__)


class GitHubIntegration:
    """Handle GitHub API interactions for repository operations."""

    def __init__(self, repo_url, token):
        """
        Initialize GitHub integration.

        :param repo_url: GitHub repository URL (e.g., https://github.com/owner/repo)
        :param token: GitHub Personal Access Token
        """
        self.token = token
        self.repo_url = repo_url.strip()

        # Parse repository owner and name
        self.owner, self.repo = self._parse_repo_url(repo_url)

        # GitHub API base URL
        self.api_base = 'https://api.github.com'

        # Setup headers
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
        }

        _logger.info('Initialized GitHub integration for %s/%s', self.owner, self.repo)

    def _parse_repo_url(self, url):
        """
        Parse GitHub repository URL to extract owner and repo name.

        :param url: Repository URL
        :return: Tuple of (owner, repo)
        """
        # Handle both https://github.com/owner/repo and github.com/owner/repo
        url = url.strip()
        if not url.startswith('http'):
            url = f'https://{url}'

        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')

        if len(path_parts) < 2:
            raise ValueError(f'Invalid GitHub repository URL: {url}')

        owner = path_parts[0]
        repo = path_parts[1].replace('.git', '')

        return owner, repo

    def _make_request(self, method, endpoint, **kwargs):
        """
        Make HTTP request to GitHub API.

        :param method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        :param endpoint: API endpoint (e.g., '/repos/owner/repo')
        :param kwargs: Additional arguments for requests
        :return: Response JSON or None
        """
        try:
            import requests
        except ImportError:
            raise ImportError(
                'Python package "requests" is not installed. '
                'Please install it: pip install requests'
            )

        url = f'{self.api_base}{endpoint}'

        # Merge headers
        headers = {**self.headers, **kwargs.pop('headers', {})}

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=30,
                **kwargs
            )

            # Log request for debugging
            _logger.debug('%s %s -> %s', method, url, response.status_code)

            # Raise for HTTP errors
            response.raise_for_status()

            # Return JSON if available
            if response.content:
                return response.json()
            return None

        except Exception as e:
            _logger.error('GitHub API request failed: %s %s - %s', method, url, str(e))
            raise

    def test_connection(self):
        """
        Test GitHub connection and return repository information.

        :return: Dict with success status and repository info
        """
        try:
            endpoint = f'/repos/{self.owner}/{self.repo}'
            repo_data = self._make_request('GET', endpoint)

            permissions = []
            if repo_data.get('permissions'):
                perms = repo_data['permissions']
                if perms.get('admin'):
                    permissions.append('admin')
                if perms.get('push'):
                    permissions.append('push')
                if perms.get('pull'):
                    permissions.append('pull')

            return {
                'success': True,
                'repo_name': repo_data.get('full_name'),
                'default_branch': repo_data.get('default_branch', 'main'),
                'permissions': permissions,
                'private': repo_data.get('private', False),
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_repo_structure(self, path=''):
        """
        Get directory structure of repository.

        :param path: Path within repository (default: root)
        :return: List of files/directories
        """
        endpoint = f'/repos/{self.owner}/{self.repo}/contents/{path}'
        return self._make_request('GET', endpoint)

    def get_file_content(self, file_path, branch='main'):
        """
        Get content of a file from repository.

        :param file_path: Path to file in repository
        :param branch: Branch name (default: main)
        :return: Decoded file content as string
        """
        endpoint = f'/repos/{self.owner}/{self.repo}/contents/{file_path}'
        params = {'ref': branch}

        response = self._make_request('GET', endpoint, params=params)

        # Decode base64 content
        if response and response.get('content'):
            content_b64 = response['content']
            content_bytes = base64.b64decode(content_b64)
            return content_bytes.decode('utf-8')

        return None

    def get_odoo_module_files(self, module_name, addons_path='addons'):
        """
        Get all Python, XML, and CSV files for an Odoo module.

        :param module_name: Name of the Odoo module
        :param addons_path: Path to addons directory in repo
        :return: List of file dictionaries with path and content
        """
        module_path = f'{addons_path}/{module_name}'

        try:
            # Get all files in module directory recursively
            all_files = self._walk_directory(module_path)

            # Filter for relevant file types
            relevant_extensions = ['.py', '.xml', '.csv']
            module_files = []

            for file_info in all_files:
                file_path = file_info['path']

                # Check extension
                if any(file_path.endswith(ext) for ext in relevant_extensions):
                    # Skip compiled Python files and cache
                    if '__pycache__' in file_path or file_path.endswith('.pyc'):
                        continue

                    # Get file content
                    try:
                        content = self.get_file_content(file_path)
                        if content:
                            module_files.append({
                                'path': file_path,
                                'name': file_info['name'],
                                'type': file_info['type'],
                                'content': content,
                            })
                    except Exception as e:
                        _logger.warning(
                            'Failed to fetch content for %s: %s',
                            file_path, str(e)
                        )
                        continue

            _logger.info(
                'Fetched %d files for module %s',
                len(module_files), module_name
            )

            return module_files

        except Exception as e:
            _logger.error(
                'Failed to get module files for %s: %s',
                module_name, str(e)
            )
            return []

    def get_app_files(self, source_path='src', file_extensions=None, max_files=25):
        """
        Get application files for non-Odoo projects.

        :param source_path: Path to source code directory (e.g., 'src', 'app', '')
        :param file_extensions: List of file extensions to include (e.g., ['.ts', '.vue'])
        :param max_files: Maximum number of files to fetch
        :return: List of file dictionaries with path and content
        """
        if file_extensions is None:
            file_extensions = ['.ts', '.js', '.vue', '.tsx', '.jsx', '.py', '.json']

        try:
            # Get all files in source directory recursively
            all_files = self._walk_directory(source_path) if source_path else self._walk_directory('')

            # Filter for relevant file types and prioritize key files
            app_files = []
            priority_patterns = [
                'package.json', 'tsconfig.json', 'vite.config', 'webpack.config',
                'main.ts', 'main.js', 'app.ts', 'app.js', 'index.ts', 'index.js',
                'App.vue', 'App.tsx', 'App.jsx',
                'router', 'store', 'api', 'service', 'composable', 'hook',
                'requirements.txt', 'pyproject.toml', 'setup.py',
            ]

            # Sort files: prioritize important files first
            def file_priority(file_info):
                path = file_info['path'].lower()
                for i, pattern in enumerate(priority_patterns):
                    if pattern.lower() in path:
                        return i
                return len(priority_patterns)

            for file_info in all_files:
                file_path = file_info['path']

                # Check extension
                if any(file_path.endswith(ext) for ext in file_extensions):
                    # Skip common non-essential directories
                    skip_patterns = [
                        'node_modules', '__pycache__', '.git', 'dist', 'build',
                        '.cache', 'coverage', '.nyc_output', '.venv', 'venv',
                        'migrations', 'test', 'tests', 'spec', '__tests__'
                    ]
                    if any(pattern in file_path for pattern in skip_patterns):
                        continue

                    app_files.append(file_info)

            # Sort by priority and limit
            app_files.sort(key=file_priority)
            app_files = app_files[:max_files]

            # Fetch content for selected files
            result_files = []
            for file_info in app_files:
                try:
                    content = self.get_file_content(file_info['path'])
                    if content:
                        # Truncate very large files
                        if len(content) > 10000:
                            content = content[:10000] + '\n\n... (truncated - file too large)'

                        result_files.append({
                            'path': file_info['path'],
                            'name': file_info['name'],
                            'type': file_info['type'],
                            'content': content,
                        })
                except Exception as e:
                    _logger.warning(
                        'Failed to fetch content for %s: %s',
                        file_info['path'], str(e)
                    )
                    continue

            _logger.info(
                'Fetched %d app files from path %s',
                len(result_files), source_path or 'root'
            )

            return result_files

        except Exception as e:
            _logger.error(
                'Failed to get app files from %s: %s',
                source_path, str(e)
            )
            return []

    def _walk_directory(self, path, max_depth=10, current_depth=0):
        """
        Recursively walk directory tree in GitHub repository.

        :param path: Starting path
        :param max_depth: Maximum recursion depth
        :param current_depth: Current recursion depth (internal)
        :return: List of all files in directory tree
        """
        if current_depth >= max_depth:
            _logger.warning('Maximum directory depth reached for path: %s', path)
            return []

        try:
            contents = self.get_repo_structure(path)
            if not contents:
                return []

            all_files = []

            for item in contents:
                if item['type'] == 'file':
                    all_files.append(item)
                elif item['type'] == 'dir':
                    # Recursively get files from subdirectory
                    subdir_files = self._walk_directory(
                        item['path'],
                        max_depth=max_depth,
                        current_depth=current_depth + 1
                    )
                    all_files.extend(subdir_files)

            return all_files

        except Exception as e:
            _logger.error('Failed to walk directory %s: %s', path, str(e))
            return []

    def get_markdown_files(self, branch='main', max_files=5):
        """
        Get markdown files from repository root and common documentation locations.

        :param branch: Branch to read from
        :param max_files: Maximum number of markdown files to fetch
        :return: List of file dictionaries with path and content
        """
        md_files = []
        priority_names = [
            'CLAUDE.md', 'README.md', 'CONTRIBUTING.md', 'ARCHITECTURE.md',
            'DEVELOPMENT.md', 'SETUP.md', 'INSTALL.md', 'CHANGELOG.md'
        ]

        try:
            # Get root directory contents
            root_contents = self.get_repo_structure('')
            if not root_contents:
                return []

            # Find markdown files in root
            root_md_files = []
            for item in root_contents:
                if item['type'] == 'file' and item['name'].lower().endswith('.md'):
                    root_md_files.append(item)

            # Sort by priority (CLAUDE.md and README.md first)
            def md_priority(file_info):
                name = file_info['name']
                for i, priority_name in enumerate(priority_names):
                    if name.lower() == priority_name.lower():
                        return i
                return len(priority_names)

            root_md_files.sort(key=md_priority)

            # Fetch content for markdown files
            for file_info in root_md_files[:max_files]:
                try:
                    content = self.get_file_content(file_info['path'], branch=branch)
                    if content:
                        md_files.append({
                            'path': file_info['path'],
                            'name': file_info['name'],
                            'content': content,
                        })
                except Exception as e:
                    _logger.warning(
                        'Failed to fetch markdown file %s: %s',
                        file_info['path'], str(e)
                    )
                    continue

            # Also check docs/ directory if it exists
            for item in root_contents:
                if item['type'] == 'dir' and item['name'].lower() in ('docs', 'doc', 'documentation'):
                    try:
                        docs_contents = self.get_repo_structure(item['path'])
                        if docs_contents:
                            for doc_item in docs_contents:
                                if (doc_item['type'] == 'file' and
                                    doc_item['name'].lower().endswith('.md') and
                                    len(md_files) < max_files):
                                    try:
                                        content = self.get_file_content(doc_item['path'], branch=branch)
                                        if content:
                                            md_files.append({
                                                'path': doc_item['path'],
                                                'name': doc_item['name'],
                                                'content': content,
                                            })
                                    except Exception:
                                        continue
                    except Exception:
                        continue

            _logger.info('Fetched %d markdown files from repository', len(md_files))
            return md_files

        except Exception as e:
            _logger.error('Failed to get markdown files: %s', str(e))
            return []

    def get_repository_files(self, file_extensions=None, max_files=30, branch='main'):
        """
        Get all relevant files from entire repository.

        :param file_extensions: List of file extensions to include
        :param max_files: Maximum number of files to fetch
        :param branch: Branch to read from
        :return: List of file dictionaries with path and content
        """
        if file_extensions is None:
            file_extensions = ['.py', '.xml', '.csv', '.ts', '.js', '.vue', '.tsx', '.jsx', '.json']

        try:
            # Walk entire repository from root
            all_files = self._walk_directory('')

            # Filter for relevant file types
            relevant_files = []
            priority_patterns = [
                # Config files
                'package.json', 'tsconfig.json', 'vite.config', 'webpack.config',
                'requirements.txt', 'pyproject.toml', 'setup.py', 'setup.cfg',
                '__manifest__.py', '__openerp__.py',
                # Entry points
                'main.ts', 'main.js', 'main.py', 'app.ts', 'app.js', 'app.py',
                'index.ts', 'index.js', 'App.vue', 'App.tsx', 'App.jsx',
                # Key patterns
                'router', 'store', 'api', 'service', 'composable', 'hook',
                'models/', 'views/', 'controllers/', 'wizard/',
            ]

            # Skip common non-essential directories
            skip_patterns = [
                'node_modules', '__pycache__', '.git', 'dist', 'build',
                '.cache', 'coverage', '.nyc_output', '.venv', 'venv',
                '.tox', '.pytest_cache', '.mypy_cache', 'htmlcov',
                'static/lib', 'static/src/lib',  # External libraries in Odoo
            ]

            for file_info in all_files:
                file_path = file_info['path']

                # Skip non-essential directories
                if any(pattern in file_path for pattern in skip_patterns):
                    continue

                # Check extension
                if any(file_path.endswith(ext) for ext in file_extensions):
                    relevant_files.append(file_info)

            # Sort by priority
            def file_priority(file_info):
                path = file_info['path'].lower()
                for i, pattern in enumerate(priority_patterns):
                    if pattern.lower() in path:
                        return i
                return len(priority_patterns)

            relevant_files.sort(key=file_priority)
            relevant_files = relevant_files[:max_files]

            # Fetch content for selected files
            result_files = []
            for file_info in relevant_files:
                try:
                    content = self.get_file_content(file_info['path'], branch=branch)
                    if content:
                        # Truncate very large files
                        if len(content) > 10000:
                            content = content[:10000] + '\n\n... (truncated - file too large)'

                        result_files.append({
                            'path': file_info['path'],
                            'name': file_info['name'],
                            'type': file_info['type'],
                            'content': content,
                        })
                except Exception as e:
                    _logger.warning(
                        'Failed to fetch content for %s: %s',
                        file_info['path'], str(e)
                    )
                    continue

            _logger.info('Fetched %d files from repository', len(result_files))
            return result_files

        except Exception as e:
            _logger.error('Failed to get repository files: %s', str(e))
            return []

    def create_branch(self, branch_name, from_branch='main'):
        """
        Create a new branch from an existing branch.

        :param branch_name: Name of the new branch
        :param from_branch: Branch to create from (default: main)
        :return: Branch creation result
        """
        try:
            # Get SHA of the from_branch
            ref_endpoint = f'/repos/{self.owner}/{self.repo}/git/ref/heads/{from_branch}'
            ref_data = self._make_request('GET', ref_endpoint)
            from_sha = ref_data['object']['sha']

            # Create new branch
            create_endpoint = f'/repos/{self.owner}/{self.repo}/git/refs'
            payload = {
                'ref': f'refs/heads/{branch_name}',
                'sha': from_sha
            }

            result = self._make_request('POST', create_endpoint, json=payload)

            _logger.info(
                'Created branch %s from %s (SHA: %s)',
                branch_name, from_branch, from_sha
            )

            return result

        except Exception as e:
            _logger.error('Failed to create branch %s: %s', branch_name, str(e))
            raise

    def create_or_update_file(self, file_path, content, message, branch):
        """
        Create or update a file in the repository.

        :param file_path: Path to file in repository
        :param content: File content (string)
        :param message: Commit message
        :param branch: Branch to commit to
        :return: Commit result
        """
        try:
            endpoint = f'/repos/{self.owner}/{self.repo}/contents/{file_path}'

            # Encode content to base64
            content_bytes = content.encode('utf-8')
            content_b64 = base64.b64encode(content_bytes).decode('utf-8')

            # Check if file exists to get SHA (required for updates)
            sha = None
            try:
                existing = self._make_request('GET', endpoint, params={'ref': branch})
                sha = existing.get('sha')
            except:
                # File doesn't exist, will be created
                pass

            # Prepare payload
            payload = {
                'message': message,
                'content': content_b64,
                'branch': branch,
            }

            if sha:
                payload['sha'] = sha

            result = self._make_request('PUT', endpoint, json=payload)

            action = 'Updated' if sha else 'Created'
            _logger.info('%s file %s on branch %s', action, file_path, branch)

            return result

        except Exception as e:
            _logger.error(
                'Failed to create/update file %s: %s',
                file_path, str(e)
            )
            raise

    def create_pull_request(self, title, body, head_branch, base_branch='main'):
        """
        Create a pull request.

        :param title: PR title
        :param body: PR description/body
        :param head_branch: Branch with changes
        :param base_branch: Target branch (default: main)
        :return: Pull request data
        """
        try:
            endpoint = f'/repos/{self.owner}/{self.repo}/pulls'

            payload = {
                'title': title,
                'body': body,
                'head': head_branch,
                'base': base_branch,
            }

            result = self._make_request('POST', endpoint, json=payload)

            _logger.info(
                'Created pull request #%s: %s',
                result.get('number'), title
            )

            return result

        except Exception as e:
            _logger.error('Failed to create pull request: %s', str(e))
            raise
