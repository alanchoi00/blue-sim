#
# Override these variables with environment variables
# e.g.
#
#   BLUE_ROS_DISTRO=iron docker buildx bake
#
# or
#
#   export BLUE_ROS_DISTRO=iron
#   docker buildx bake
#
variable "BLUE_ROS_DISTRO" { default = "jazzy" }
variable "BLUE_GITHUB_REPO" { default = "alanchoi00/blue-sim" }

group "default" {
  targets = ["ci", "robot", "desktop", "desktop-nvidia"]
}

# These are populated by the metadata-action Github action for each target
# when building in CI
#
target "docker-metadata-action-ci" {}
target "docker-metadata-action-robot" {}
target "docker-metadata-action-desktop" {}
target "docker-metadata-action-desktop-nvidia" {}


#
# All images can pull cache from the images published at Github
# or local storage (within the Buildkit image)
#
# ... and push cache to local storage
#
target "ci" {
  inherits = ["docker-metadata-action-ci"]
  dockerfile = ".docker/Dockerfile"
  target = "ci"
  context = ".."
  tags = [
    "ghcr.io/${BLUE_GITHUB_REPO}:${BLUE_ROS_DISTRO}-ci"
  ]
  labels = {
    "org.opencontainers.image.source" = "https://github.com/${BLUE_GITHUB_REPO}"
  }
  platforms = ["linux/amd64", "linux/arm64"]
}

target "robot" {
  inherits = ["docker-metadata-action-robot"]
  dockerfile = ".docker/Dockerfile"
  target = "robot"
  context = ".."
  tags = [
    "ghcr.io/${BLUE_GITHUB_REPO}:${BLUE_ROS_DISTRO}-robot"
  ]
  labels = {
    "org.opencontainers.image.source" = "https://github.com/${BLUE_GITHUB_REPO}"
  }
  platforms = ["linux/amd64", "linux/arm64"]
}

target "desktop" {
  inherits = ["docker-metadata-action-desktop"]
  dockerfile = ".docker/Dockerfile"
  target = "desktop"
  context = ".."
  args = {
    ROS_DISTRO = "${BLUE_ROS_DISTRO}"
  }
  tags = [
    "ghcr.io/${BLUE_GITHUB_REPO}:${BLUE_ROS_DISTRO}-desktop"
  ]
  labels = {
    "org.opencontainers.image.source" = "https://github.com/${BLUE_GITHUB_REPO}"
  }
  platforms = ["linux/amd64"]
}

target "desktop-nvidia" {
  inherits = ["desktop", "docker-metadata-action-desktop-nvidia"]
  target = "desktop-nvidia"
  tags = [
    "ghcr.io/${BLUE_GITHUB_REPO}:${BLUE_ROS_DISTRO}-desktop-nvidia"
  ]
}
