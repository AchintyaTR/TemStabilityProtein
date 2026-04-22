import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor

def download_single(uid, output_dir):
    output_path = os.path.join(output_dir, f"{uid}.pdb")
    if os.path.exists(output_path):
        return f"Skipped {uid}"
        
    api_url = f"https://alphafold.ebi.ac.uk/api/prediction/{uid}"
    try:
        api_resp = requests.get(api_url, timeout=10)
        if api_resp.status_code == 200:
            data = api_resp.json()
            if isinstance(data, list) and len(data) > 0:
                pdb_url = data[0].get('pdbUrl')
                if pdb_url:
                    pdb_resp = requests.get(pdb_url, timeout=30)
                    if pdb_resp.status_code == 200:
                        with open(output_path, 'wb') as f:
                            f.write(pdb_resp.content)
                        return f"Downloaded {uid}"
                    else:
                        return f"Failed PDB fetch {uid}"
        elif api_resp.status_code == 404:
            return f"Not found 404 {uid}"
    except Exception as e:
        return f"Error {uid}: {e}"
    return f"Failed API {uid}"

def download_structures(ids_file='uniprot_ids.txt', output_dir='alphafold_structures', max_workers=10):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    if not os.path.exists(ids_file):
        print(f"Error: {ids_file} not found.")
        return

    with open(ids_file, 'r') as f:
        uniprot_ids = [line.strip() for line in f if line.strip()]

    print(f"Found {len(uniprot_ids)} IDs to process.")
    
    print(f"Starting parallel download with {max_workers} workers...")
    success_count = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_single, uid, output_dir): uid for uid in uniprot_ids}
        for i, future in enumerate(futures):
            res = future.result()
            if "Downloaded" in res or "Skipped" in res:
                success_count += 1
            if (i + 1) % 500 == 0:
                print(f"Processed {i + 1}/{len(uniprot_ids)} | Valid: {success_count}", flush=True)

    print("Download process completed.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Download AlphaFold structures.')
    parser.add_argument('--input', default='uniprot_ids.txt', help='Path to input IDs file')
    parser.add_argument('--output', default='alphafold_structures', help='Path to output directory')
    args = parser.parse_args()

    download_structures(ids_file=args.input, output_dir=args.output)

