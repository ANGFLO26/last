#!/bin/bash

# Script để cài Spark Client trên Airflow Machine
# Chỉ cần client, không cần full cluster

echo "=========================================="
echo "Installing Spark Client on Airflow Machine"
echo "=========================================="

# Check if Spark is already installed
if command -v spark-submit &> /dev/null; then
    echo "Spark is already installed:"
    spark-submit --version
    exit 0
fi

# Check if SPARK_HOME is set
if [ -n "$SPARK_HOME" ] && [ -f "$SPARK_HOME/bin/spark-submit" ]; then
    echo "Spark found at SPARK_HOME: $SPARK_HOME"
    echo "Adding to PATH..."
    export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin
    spark-submit --version
    exit 0
fi

# Check if Spark exists in /opt/spark
if [ -d "/opt/spark" ] && [ -f "/opt/spark/bin/spark-submit" ]; then
    echo "Spark found at /opt/spark"
    export SPARK_HOME=/opt/spark
    export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin
    spark-submit --version
    exit 0
fi

# Download and install Spark
echo "Spark not found. Installing..."

SPARK_VERSION="3.5.0"
SPARK_URL="https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz"
INSTALL_DIR="/opt"
SPARK_HOME_DIR="${INSTALL_DIR}/spark"

# Check if running as root or has sudo
if [ "$EUID" -ne 0 ]; then
    SUDO="sudo"
else
    SUDO=""
fi

echo "Downloading Spark ${SPARK_VERSION}..."
cd /tmp
wget -q --show-progress "$SPARK_URL" || {
    echo "Error: Failed to download Spark"
    exit 1
}

echo "Extracting Spark..."
tar -xzf "spark-${SPARK_VERSION}-bin-hadoop3.tgz"

echo "Installing to ${SPARK_HOME_DIR}..."
$SUDO mkdir -p "$INSTALL_DIR"
$SUDO rm -rf "$SPARK_HOME_DIR"
$SUDO mv "spark-${SPARK_VERSION}-bin-hadoop3" "$SPARK_HOME_DIR"

# Set permissions
$SUDO chown -R $USER:$USER "$SPARK_HOME_DIR" 2>/dev/null || true

# Set environment variables
echo ""
echo "Setting environment variables..."
echo ""
echo "Add these lines to your ~/.bashrc or ~/.profile:"
echo "export SPARK_HOME=${SPARK_HOME_DIR}"
echo "export PATH=\$PATH:\$SPARK_HOME/bin:\$SPARK_HOME/sbin"
echo ""

# Add to current session
export SPARK_HOME="$SPARK_HOME_DIR"
export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin

# Verify installation
echo "Verifying installation..."
if [ -f "$SPARK_HOME/bin/spark-submit" ]; then
    echo "✓ Spark installed successfully!"
    echo ""
    echo "Spark version:"
    "$SPARK_HOME/bin/spark-submit" --version
    echo ""
    echo "To make it permanent, add to ~/.bashrc:"
    echo "  export SPARK_HOME=${SPARK_HOME_DIR}"
    echo "  export PATH=\$PATH:\$SPARK_HOME/bin:\$SPARK_HOME/sbin"
    echo ""
    echo "Then run: source ~/.bashrc"
else
    echo "✗ Installation failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "Spark Client Installation Complete!"
echo "=========================================="
echo ""
echo "Test connection to Spark cluster:"
echo "  spark-submit --master spark://192.168.1.134:7077 --version"

