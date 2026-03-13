#
# Dockerfile for *-robot development container
#
ARG BLUE_GITHUB_REPO=Robotic-Decision-Making-Lab/blue
ARG ROS_DISTRO=humble
FROM ${BLUE_GITHUB_REPO}:${ROS_DISTRO}-robot

# Install ROS dependencies
# This is done in a previous stage, but we include it again here in case anyone wants to
# add new dependencies during development
ENV USERNAME=blue
ENV USER_WORKSPACE=/home/$USERNAME/ws_blue
WORKDIR $USER_WORKSPACE

COPY --chown=blue:blue . src/blue
# Bypass expired ROS2 GPG key (F42ED6FBAB17C654) - works for both legacy .list and DEB822 .sources formats
RUN sudo sed -i 's|signed-by=/usr/share/keyrings/ros-archive-keyring.gpg||g' \
        /etc/apt/sources.list.d/*.list 2>/dev/null || true \
    && sudo sed -i '/^Signed-By/d' /etc/apt/sources.list.d/*.sources 2>/dev/null || true \
    && echo 'Acquire::AllowInsecureRepositories "true";' | sudo tee /etc/apt/apt.conf.d/99-ros-insecure > /dev/null \
    && echo 'APT::Get::AllowUnauthenticated "true";' | sudo tee -a /etc/apt/apt.conf.d/99-ros-insecure > /dev/null
RUN sudo apt-get -q update \
    && sudo apt-get -q -y upgrade \
    && rosdep update \
    && rosdep install -y --from-paths src --ignore-src --rosdistro ${ROS_DISTRO} --skip-keys="gz-transport12 gz-sim7 gz-math7 gz-msgs9 gz-plugin2" \
    && sudo apt-get autoremove -y \
    && sudo apt-get clean -y \
    && sudo rm -rf /var/lib/apt/lists/*

# Install debugging/linting Python packages
RUN python3 -m pip install \
    pre-commit \
    mypy

# Disable the setuputils installation warning
# This prevents us from needing to pin the setuputils version (which doesn't always work)
ENV PYTHONWARNINGS="ignore"
