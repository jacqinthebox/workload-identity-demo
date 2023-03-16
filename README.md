# Workload Identity Demo

## How it works

https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview

![image](https://user-images.githubusercontent.com/361399/225572771-203381c9-99fc-4585-8a96-eba78ab01eb7.png)


## Build cluster

Create a cluster with support for Workload Identity

```sh
az extension add --name aks-preview
az feature register --namespace "Microsoft.ContainerService" --name "EnableWorkloadIdentityPreview"


PREFIX=demo01-dev-we
az group create -n $PREFIX-rg --location westeurope

az aks create -g $PREFIX-rg -n $PREFIX-cluster --node-count 2 --location westeurope \
	--network-plugin azure \
	--node-resource-group $PREFIX-nodes-rg --max-pods 110 \
	--enable-aad --enable-azure-rbac --node-vm-size Standard_B2ms \
	--enable-oidc-issuer --enable-workload-identity
```

Next check the well-known url from the cluster:

```sh
export AKS_OIDC_ISSUER="$(az aks show -n $PREFIX-cluster -g $PREFIX-rg --query "oidcIssuerProfile.issuerUrl" -otsv)"
echo $AKS_OIDC_ISSUER
```
## Create managed identity and service account

Next create a managed identity and get the client id. 


```sh
IDENTITY=$PREFIX-identity 
export SUBSCRIPTION_ID="$(az account show --query "id" -otsv)" 

az identity create --name $IDENTITY --resource-group $PREFIX-rg --location westeurope --subscription $SUBSCRIPTION_ID 

export USER_ASSIGNED_CLIENT_ID="$(az identity show -n $IDENTITY -g $PREFIX-rg --query "clientId" -otsv)" 
echo $USER_ASSIGNED_CLIENT_ID
```

With the client_id you can create a service account:

```sh
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  annotations:
    azure.workload.identity/client-id: $USER_ASSIGNED_CLIENT_ID
  labels:
    azure.workload.identity/use: "true"
  name: workload-identity-serviceaccount
  namespace: default
EOF
```

## Enable it for federation

Next, create a federated credential:

```sh
# these variables where already set earlier
# IDENTITY=$PREFIX-identity
# AKD_OIDC_ISSUER=your_oidc_issuer

az identity federated-credential create --name federated-identity-sademo \
  --identity-name $IDENTITY \
  --resource-group $PREFIX-rg --issuer ${AKS_OIDC_ISSUER} \
  --subject system:serviceaccount:default:workload-identity-serviceaccount
```

## Test

Let's test it with storage


```sh
az storage account create \
  --name demo01devwestorage \
  --resource-group $PREFIX-rg \
  --location westeurope
```

Next give the managed identity access to the storage account.


```sh
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-worker-deployment
  namespace: default
  labels:
    app: python-worker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: python-worker
  template:
    metadata:
      labels:
        app: python-worker
        azure.workload.identity/use: "true"
    spec:
      serviceAccount: workload-identity-serviceaccount
      containers:
        - name: python-worker
          image: ghcr.io/jacqinthebox/python-worker:latest
EOF
```
