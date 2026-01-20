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
